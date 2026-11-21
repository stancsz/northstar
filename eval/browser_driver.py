"""A local ChromeDriver client executed inside the evaluation container."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ENDPOINT = "http://127.0.0.1:9515"
SESSION = Path("/tmp/spot-advisor-browser-session")
ELEMENT_ID = "element-6066-11e4-a52e-4f735466cecf"


def request(path: str, payload: dict | None = None, *, timeout: float = 8):
    data = json.dumps(payload).encode() if payload is not None else None
    with urlopen(Request(ENDPOINT + path, data=data, headers={"Content-Type": "application/json"}), timeout=timeout) as result:
        return json.load(result)["value"]


def open_fixture():
    for i in range(20):
        try:
            request("/status")
            break
        except URLError:
            if i == 19:
                raise
            time.sleep(0.15)
    result = request("/session", {"capabilities": {"alwaysMatch": {
        "browserName": "chrome",
        "goog:chromeOptions": {"args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
                                       "--disable-background-networking", "--no-first-run"]},
    }}}, timeout=30)
    SESSION.write_text(result["sessionId"])
    command("/url", {"url": "file:///work/index.html"})


def command(path: str, payload: dict | None = None):
    return request("/session/" + SESSION.read_text() + path, payload)


def script(source: str, *args):
    return command("/execute/sync", {"script": source, "args": args})


def control(label: str, kind: str) -> str:
    element = script(
        "return [...document.querySelectorAll(arguments[1])].find(e => "
        "e.getClientRects().length && (e.getAttribute('aria-label') || e.textContent.trim()) === arguments[0]) || null;",
        label, kind,
    )
    if not element:
        raise ValueError("No visible control matches the exact label.")
    return "/element/" + element[ELEMENT_ID]


def act(action: str, label: str | None, value: str | None):
    if action == "observe":
        return script(
            "return document.body.innerText.trim() + '\\n' + [...document.querySelectorAll('select, textarea')]"
            ".filter(e => e.getClientRects().length).map(e => e.getAttribute('aria-label') + ': ' + e.value "
            "+ (e.options ? ' (options: ' + [...e.options].map(o => o.text).join(', ') + ')' : '')).join('\\n');"
        )
    if action == "click":
        command(control(label, "button") + "/click", {})
    elif action == "fill":
        target = control(label, "textarea")
        command(target + "/clear", {})
        command(target + "/value", {"text": value})
    elif action == "select":
        element = control(label, "select").split("/")[-1]
        select = {ELEMENT_ID: element}
        option = script("return [...arguments[0].options].find(o => o.text === arguments[1]) || null;", select, value)
        if not option:
            raise ValueError("No option matches the exact label.")
        command("/element/" + option[ELEMENT_ID] + "/click", {})
    return act("observe", None, None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "state", "observe", "click", "fill", "select"))
    parser.add_argument("--label")
    parser.add_argument("--value")
    args = parser.parse_args()
    try:
        if args.action == "start":
            open_fixture()
        elif args.action == "state":
            print(json.dumps(script("return window.deskState();")))
        else:
            print(act(args.action, args.label, args.value))
    except (ValueError, URLError, TimeoutError) as exc:
        print(f"Chromium action failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
