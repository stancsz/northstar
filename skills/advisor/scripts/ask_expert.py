#!/usr/bin/env python3
"""Ask a frontier advisor model for short, turn-based Verdict/Next/Prompt/Risk advice."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TextIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


MAX_PACKET_CHARS = 4_000
MAX_IMAGES = 8
MAX_IMAGE_BYTES = 10_000_000
MAX_TOTAL_IMAGE_BYTES = 20_000_000
MAX_INPUT_TOKENS = 32_000
MAX_CODEX_REQUEST_BYTES = 24_000
CODEX_API_BASE_URL = "https://chatgpt.com/backend-api/codex"
DIRECT_CODEX_MODELS = frozenset({"gpt-6.1-terra", "gpt-6.1-sol"})


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an Advisor credential to a different host.
        return None


urlopen = build_opener(NoRedirect).open


class AdvisorGatewayUnavailable(RuntimeError):
    """The gateway cannot be reached before model inference begins."""


DEFAULT_ADVISOR_MODEL = os.environ.get("NORTHSTAR_ADVISOR_MODEL", "gpt-6.1-terra")

ADVISOR_INSTRUCTION = """You are a concise, high-signal technical advisor, not the task executor.
The caller agent will do all file reading, coding, and testing in short turns.
Do NOT repeat the packet, lecture, write large code blocks, use tools, or claim verification.
Return exactly these four lines, with no preamble or markdown fences:
Verdict: one decisive sentence answering the question.
Next: at most three short, testable actions for the caller.
Prompt: one short, ready-to-execute next-turn instruction for the caller.
Risk: one material risk or stop condition, or `none`.
Keep the entire response under 150 words."""

VISUAL_INSTRUCTION = """You are a concise visual advisor, not the implementation worker.
Inspect the attached images yourself. Name concrete observations tied to visible regions;
do not infer unseen detail, write code, or claim verification.
Return exactly these four lines, with no preamble or markdown fences:
Verdict: visible observations and the current visual judgment.
Next: concrete, prioritized UI fixes or exact crops/states needed next.
Prompt: one short, ready-to-execute next-turn instruction for the caller.
Risk: unreadable details, missing evidence, or a material stop condition, or `none`.
Keep the response under 400 words."""


def configure_utf8_stdout(stdout: TextIO | None = None) -> None:
    """Make JSON advice readable on Windows consoles using legacy code pages."""
    stream = sys.stdout if stdout is None else stdout
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="backslashreplace")


def windows_user_env(name: str) -> str | None:
    """Read persisted user configuration when a desktop parent has a stale environment."""
    if sys.platform != "win32":
        return None
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, kind = winreg.QueryValueEx(key, name)
        if kind == winreg.REG_SZ and isinstance(value, str) and value.strip():
            return value
    except OSError:
        pass
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_ADVISOR_MODEL,
                        help="Exact model name for the advisor.")
    parser.add_argument("--transport", choices=("auto", "gateway", "codex", "claude"), default="auto",
                        help="Select gateway, direct Codex, direct Claude CLI, or auto fallback.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input-file", type=Path)
    source.add_argument("--question")
    parser.add_argument(
        "--base-url",
        default=(
            os.environ["EXPERTS_BASE_URL"]
            if "EXPERTS_BASE_URL" in os.environ
            else (windows_user_env("EXPERTS_BASE_URL") or "")
        ),
        help="Advisor API base URL (or set EXPERTS_BASE_URL).",
    )
    parser.add_argument("--timeout-seconds", type=float, default=75.0)
    parser.add_argument("--image", type=Path, action="append", default=[],
                        help="Attach a local PNG/JPEG/WebP/GIF; repeat for views/crops.")
    parser.add_argument("--image-detail", choices=("auto", "low", "high"), default="high")
    return parser.parse_args()


def read_packet(args: argparse.Namespace) -> str:
    packet = args.question
    if args.input_file is not None:
        try:
            packet = args.input_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"Unable to read advisor packet: {exc}") from exc
    assert packet is not None
    packet = packet.strip()
    if not packet:
        raise SystemExit("Advisor packet must not be empty.")
    if len(packet) > MAX_PACKET_CHARS:
        raise SystemExit(
            f"Advisor packet is {len(packet)} characters; limit is {MAX_PACKET_CHARS}. "
            "Summarize the facts and ask one sharp question instead of dumping raw context."
        )
    return packet


def prepare_images(paths: list[Path], detail: str = "high") -> tuple[list[dict], list[dict]]:
    """Read explicit attachments before any call; keep pixels out of receipts."""
    if len(paths) > MAX_IMAGES:
        raise ValueError(f"At most {MAX_IMAGES} images per call; split the requested views into batches.")
    parts, receipts, total = [], [], 0
    for index, path in enumerate(paths, 1):
        path = path.resolve(strict=True)
        if not path.is_file() or path.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError(f"Image {index} must be a file no larger than {MAX_IMAGE_BYTES} bytes.")
        with path.open("rb") as stream:
            data = stream.read(MAX_IMAGE_BYTES + 1)
        total += len(data)
        if len(data) > MAX_IMAGE_BYTES or total > MAX_TOTAL_IMAGE_BYTES:
            raise ValueError("Image byte budget exceeded; split the requested views into batches.")
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"
        elif data.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        elif data.startswith((b"GIF87a", b"GIF89a")):
            mime = "image/gif"
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            mime = "image/webp"
        else:
            raise ValueError(f"Image {index} is not a supported PNG/JPEG/WebP/GIF image.")
        try:
            from io import BytesIO
            from PIL import Image, UnidentifiedImageError

            with Image.open(BytesIO(data)) as decoded:
                if decoded.format not in {"PNG", "JPEG", "GIF", "WEBP"}:
                    raise ValueError(f"Image {index} is not a supported PNG/JPEG/WebP/GIF image.")
                decoded.load()
        except ImportError as exc:
            raise ValueError("Image validation requires the already-installed Pillow package.") from exc
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError(f"Image {index} is malformed or truncated.") from exc
        parts.extend([
            {"type": "text", "text": f"Attached image {index}: {path.name}"},
            {"type": "image_url", "image_url": {
                "url": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}",
                "detail": detail,
            }},
        ])
        receipts.append({"image": index, "path": str(path), "mime_type": mime,
                         "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                         "detail": detail})
    return parts, receipts


def with_images(messages: list[dict], parts: list[dict]) -> list[dict]:
    """Attach image parts to the final user message."""
    if not parts:
        return messages
    result = [dict(message) for message in messages]
    for message in reversed(result):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            if not isinstance(content, list):
                raise ValueError("Image consultation needs user text or content blocks.")
            message["content"] = [*content, *parts]
            return result
    raise ValueError("Image consultation needs a user message.")


def responses_input(messages: list[dict]) -> list[dict]:
    """Translate Chat Completions messages to equivalent Responses count input."""
    result = []
    for message in messages:
        if not isinstance(message, dict) or set(message) != {"role", "content"}:
            raise ValueError("Advisor token preflight received an unsupported message shape.")
        role, content = message["role"], message["content"]
        if role not in {"system", "developer", "user", "assistant"}:
            raise ValueError("Advisor token preflight received an unsupported message role.")
        if isinstance(content, str):
            converted = content
        elif isinstance(content, list):
            converted = []
            for block in content:
                if not isinstance(block, dict):
                    raise ValueError("Advisor token preflight received an unsupported content block.")
                if block.get("type") in {"text", "input_text"} and isinstance(block.get("text"), str):
                    converted.append({"type": "input_text", "text": block["text"]})
                elif block.get("type") == "image_url":
                    image = block.get("image_url")
                    if (not isinstance(image, dict) or set(image) - {"url", "detail"}
                            or not isinstance(image.get("url"), str)):
                        raise ValueError("Advisor token preflight received an unsupported image block.")
                    converted.append({"type": "input_image", "image_url": image["url"],
                                      "detail": image.get("detail", "auto")})
                else:
                    raise ValueError("Advisor token preflight received an unsupported content block.")
        else:
            raise ValueError("Advisor token preflight received unsupported message content.")
        result.append({"role": role, "content": converted})
    return result


def count_input_tokens(args: argparse.Namespace, model: str, messages: list[dict], api_key: str | None) -> int:
    """Ask the configured route for exact text/image tokens before model submission."""
    payload = {"model": model, "input": responses_input(messages)}
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(
        f"{args.base_url.rstrip('/')}/responses/input_tokens",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=args.timeout_seconds) as response:
            body = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if api_key:
            detail = detail.replace(api_key, "[REDACTED]")
        detail = detail[:1_000]
        if exc.code == 401:
            raise RuntimeError(
                "Advisor token preflight returned HTTP 401: set EXPERTS_API_KEY; no model request was sent."
            ) from exc
        raise RuntimeError(f"Advisor token preflight returned HTTP {exc.code}: {detail}; no model request was sent.") from exc
    except (URLError, TimeoutError) as exc:
        raise AdvisorGatewayUnavailable(
            f"Advisor token preflight is unavailable; no model request was sent: {exc}"
        ) from exc
    count = body.get("input_tokens") if isinstance(body, dict) else None
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise RuntimeError("Advisor token preflight returned no valid input_tokens count; no model request was sent.")
    return count


def expert_api_key(base_url: str) -> str | None:
    if "EXPERTS_API_KEY" in os.environ:
        return os.environ["EXPERTS_API_KEY"] or None
    endpoint = urlsplit(base_url)
    local = (endpoint.scheme == "http" and endpoint.hostname in ("127.0.0.1", "localhost", "::1")
             and endpoint.username is None and endpoint.password is None)
    if local and endpoint.port is not None:
        return windows_user_env("EXPERTS_API_KEY")
    return None


def call_gateway(args: argparse.Namespace, model: str, messages: list[dict]) -> dict:
    if not getattr(args, "base_url", None) or not str(args.base_url).strip():
        raise AdvisorGatewayUnavailable(
            "Advisor API base URL is not configured; set EXPERTS_BASE_URL or pass --base-url."
        )
    started = time.monotonic()
    api_key = expert_api_key(args.base_url)
    full_messages = with_images(messages, getattr(args, "image_parts", []))
    input_tokens = count_input_tokens(args, model, full_messages, api_key)
    if input_tokens > MAX_INPUT_TOKENS:
        raise RuntimeError(
            f"Advisor request requires {input_tokens:,} input tokens; the limit is {MAX_INPUT_TOKENS:,}. "
            "Reduce the text or image detail/dimensions; no model request was sent."
        )
    payload = {
        "model": model,
        "reasoning_effort": "low",
        "stream": False,
        "messages": full_messages,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    endpoint = f"{args.base_url.rstrip('/')}/chat/completions"
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=args.timeout_seconds) as response:
            body = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if api_key:
            detail = detail.replace(api_key, "[REDACTED]")
        detail = detail[:1_000]
        if exc.code == 401:
            raise RuntimeError(
                "Expert API returned HTTP 401: service authentication failed. "
                "Set EXPERTS_API_KEY (Windows user environment is read for local loopback). "
                "No retry was made."
            ) from exc
        raise RuntimeError(f"Expert API returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Expert API is unavailable: {exc}") from exc

    try:
        choice = body["choices"][0]
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Expert API returned no usable advisor content.") from exc
    if choice.get("finish_reason") != "stop":
        raise RuntimeError("Expert API did not return a completed answer.")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Expert API returned empty advisor content.")

    return {
        "model": body.get("model", model),
        "requested_model": model,
        "transport": "gateway",
        "advice": content.strip(),
        "advice_words": len(content.split()),
        "usage": body.get("usage"),
        "input_tokens": input_tokens,
        "request_id": body.get("id"),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def codex_auth_path() -> Path:
    auth_file_value = os.environ.get("CODEX_AUTH_FILE")
    if auth_file_value:
        return Path(auth_file_value)
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    return codex_home / "auth.json"


def read_codex_credentials() -> tuple[str, str]:
    """Read the existing Codex access token and account id without displaying either."""
    auth_path = codex_auth_path()
    try:
        tokens = json.loads(auth_path.read_text(encoding="utf-8"))["tokens"]
        access_token = tokens["access_token"]
        account_id = tokens["account_id"]
        if not all(isinstance(value, str) and value.strip() for value in (access_token, account_id)):
            raise ValueError("Codex auth file contains an invalid token or account id")
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Unable to read Codex credentials from {auth_path}; sign in with `codex login`."
        ) from exc
    return access_token, account_id


def codex_stream_events(response):
    """Yield parsed Codex Responses events from an SSE stream."""
    data_lines = []
    for raw_line in response:
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip(" ").rstrip("\r\n"))
        elif not line.strip() and data_lines:
            data = "\n".join(data_lines)
            data_lines.clear()
            if data == "[DONE]":
                return
            try:
                event = json.loads(data)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Codex returned a malformed streaming event.") from exc
            if not isinstance(event, dict):
                raise RuntimeError("Codex returned an invalid streaming event.")
            yield event
    if data_lines:
        raise RuntimeError("Codex response stream ended before the last event boundary.")


def consult_codex(
    args: argparse.Namespace,
    messages: list[dict],
    *,
    fallback_reason: str | None = None,
) -> dict:
    """Send one bounded text consultation directly to the authenticated Codex API."""
    model = args.model
    if model not in DIRECT_CODEX_MODELS:
        raise RuntimeError(
            "Direct Codex supports only gpt-6.1-terra and gpt-6.1-sol; "
            "select one with --model or NORTHSTAR_ADVISOR_MODEL."
        )
    access_token, account_id = read_codex_credentials()
    payload = {
        "model": model,
        "stream": True,
        "store": False,
        "reasoning": {"effort": "low"},
        "input": responses_input(messages),
    }
    request_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(request_body) > MAX_CODEX_REQUEST_BYTES:
        raise RuntimeError(
            f"Direct Codex request is {len(request_body):,} bytes; "
            f"the limit is {MAX_CODEX_REQUEST_BYTES:,} bytes. Shorten the packet."
        )
    request = Request(
        f"{CODEX_API_BASE_URL}/responses",
        data=request_body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "ChatGPT-Account-ID": account_id,
            "User-Agent": f"OpenAI-Codex/0.154.0 ({platform.system()})",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )
    started = time.monotonic()
    output_text = []
    terminal = None
    try:
        with urlopen(request, timeout=args.timeout_seconds) as response:
            for event in codex_stream_events(response):
                event_type = event.get("type")
                if event_type in {"response.failed", "response.incomplete", "error"}:
                    raise RuntimeError("Codex advisor stream failed or was incomplete.")
                if event_type == "response.output_text.delta":
                    delta = event.get("delta")
                    if terminal is not None or not isinstance(delta, str):
                        raise RuntimeError("Codex advisor stream contained an invalid text delta.")
                    output_text.append(delta)
                elif event_type == "response.completed":
                    if terminal is not None:
                        raise RuntimeError("Codex advisor stream contained duplicate completion events.")
                    terminal = event.get("response")
                    if not isinstance(terminal, dict) or terminal.get("status") != "completed":
                        raise RuntimeError("Codex advisor stream did not complete successfully.")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        detail = detail.replace(access_token, "[REDACTED]")
        detail = detail.replace(account_id, "[REDACTED]")[:1_000]
        if exc.code == 401:
            raise RuntimeError(
                "Codex authentication was rejected or expired; refresh it with `codex login`."
            ) from exc
        raise RuntimeError(f"Codex advisor API returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Codex advisor API is unavailable: {exc}") from exc

    if terminal is None:
        raise RuntimeError("Codex advisor stream ended without a completed response.")
    actual_model = terminal.get("model")
    if actual_model != model:
        raise RuntimeError(
            f"Codex returned model {actual_model!r}, expected requested model {model!r}."
        )
    request_id = terminal.get("id")
    if not isinstance(request_id, str) or not request_id:
        raise RuntimeError("Codex completed response omitted its response ID.")
    advice = "".join(output_text).strip()
    if not advice:
        raise RuntimeError("Codex completed response contained no advisor text.")
    usage = terminal.get("usage")
    if not isinstance(usage, dict) or any(
        type(usage.get(key)) is not int or usage[key] < 0
        for key in ("input_tokens", "output_tokens", "total_tokens")
    ):
        raise RuntimeError("Codex completed response omitted valid provider usage.")
    return {
        "model": actual_model,
        "requested_model": model,
        "transport": "codex",
        "fallback_reason": fallback_reason,
        "advice": advice,
        "advice_words": len(advice.split()),
        "usage": usage,
        "input_tokens": usage["input_tokens"],
        "request_id": request_id,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def consult_claude(
    args: argparse.Namespace,
    instruction: str,
    packet: str,
    *,
    fallback_reason: str | None = None,
) -> dict:
    """Send one bounded, tool-free text consultation via the local Claude Code CLI."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        raise RuntimeError("Claude Code CLI (`claude`) was not found on PATH.")
    started = time.monotonic()
    command = [
        claude_bin,
        "-p",
        "--no-session-persistence",
        "--output-format", "json",
        "--tools", "",
        "--system-prompt", instruction,
    ]
    if args.model and args.model not in DIRECT_CODEX_MODELS:
        command.extend(["--model", args.model])
    try:
        completed = subprocess.run(
            command,
            input=packet,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=args.timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Claude Code CLI consultation failed: {exc}") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[:1_000]
        raise RuntimeError(f"Claude Code CLI exited {completed.returncode}: {detail}")

    try:
        body = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Claude Code CLI returned malformed JSON.") from exc

    if not isinstance(body, dict) or body.get("is_error"):
        raise RuntimeError(f"Claude Code CLI reported an error: {body.get('result', 'unknown error')}")

    advice = str(body.get("result") or "").strip()
    if not advice:
        raise RuntimeError("Claude Code CLI returned empty advisor content.")

    return {
        "model": args.model if (args.model and args.model not in DIRECT_CODEX_MODELS) else "claude-cli-default",
        "requested_model": args.model,
        "transport": "claude",
        "fallback_reason": fallback_reason,
        "advice": advice,
        "advice_words": len(advice.split()),
        "usage": body.get("usage"),
        "request_id": body.get("session_id"),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def main() -> int:
    configure_utf8_stdout()
    args = parse_args()
    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be positive.")

    transport = getattr(args, "transport", "auto")
    if transport in {"codex", "claude"} and args.image:
        raise SystemExit(
            f"Direct {transport} transport supports text packets only; image attachments require the Advisor gateway."
        )

    packet = read_packet(args)
    try:
        args.image_parts, images = prepare_images(args.image, args.image_detail)
        instruction = VISUAL_INSTRUCTION if images else ADVISOR_INSTRUCTION
        messages = [
            {"role": "developer", "content": instruction},
            {"role": "user", "content": packet},
        ]

        if transport == "codex":
            result = consult_codex(args, messages)
        elif transport == "claude":
            result = consult_claude(args, instruction, packet)
        else:
            try:
                result = call_gateway(args, args.model, messages)
            except AdvisorGatewayUnavailable as exc:
                if transport != "auto":
                    raise
                if images:
                    raise RuntimeError(
                        f"{exc} Direct CLI fallback supports text consultations only; images require the Advisor gateway."
                    ) from exc
                if args.model in DIRECT_CODEX_MODELS and codex_auth_path().is_file():
                    result = consult_codex(args, messages, fallback_reason=str(exc))
                elif shutil.which("claude"):
                    result = consult_claude(args, instruction, packet, fallback_reason=str(exc))
                elif codex_auth_path().is_file():
                    result = consult_codex(args, messages, fallback_reason=str(exc))
                else:
                    raise RuntimeError(
                        f"{exc} No local Codex auth or Claude CLI fallback was available."
                    ) from exc

        result.setdefault("transport", "gateway")
        result.setdefault("fallback_reason", None)
        if images:
            result["images"] = images
        result["packet_chars"] = len(packet)
    except (RuntimeError, ValueError, OSError) as exc:
        print(json.dumps({"status": "unavailable", "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status", "ok") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
