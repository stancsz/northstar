"""Launch one isolated Codex CLI worker; no implicit native-agent fallback."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import uuid


CONFIG = '''model_provider = "openrouter"

[model_providers.openrouter]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
env_key = "OPENROUTER_API_KEY"
wire_api = "responses"
requires_openai_auth = false
'''


class ProcessTreeCleanupError(Exception):
    """The root stopped, but stopping all descendants was not verified."""


def run_worker(command, *, input, stdout, stderr, env, timeout, **_):
    """Run one CLI process with a deadline and stop its process tree on timeout."""
    options = {'start_new_session': True} if os.name != 'nt' else {}
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                               text=True, env=env, **options)
    try:
        process.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            try:
                stopped = subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                         timeout=10, check=False)
                tree_stopped = stopped.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                tree_stopped = False
            if not tree_stopped:
                if process.poll() is None:
                    process.kill()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
                raise ProcessTreeCleanupError('Descendant cleanup could not be verified')
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            raise ProcessTreeCleanupError('Worker termination could not be verified')
        raise
    return subprocess.CompletedProcess(command, process.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    parser.add_argument('--assignment', required=True, type=Path)
    parser.add_argument('--receipts', required=True, type=Path)
    parser.add_argument('--codex-executable', required=True, type=Path)
    parser.add_argument('--model', default='minimax/minimax-m3.1-flash')
    parser.add_argument('--disable-plugins', action='store_true')
    parser.add_argument('--sandbox', choices=('read-only', 'workspace-write'), default='read-only')
    args = parser.parse_args()
    if not os.environ.get('OPENROUTER_API_KEY', '').strip():
        parser.error('OPENROUTER_API_KEY must already be present in the environment')
    workdir = args.workdir.resolve(strict=True)
    if not workdir.is_dir():
        parser.error('workdir must be a directory')
    assignment = args.assignment.read_text(encoding='utf-8')
    if not assignment.strip() or not args.model.strip():
        parser.error('assignment and model must not be empty')
    args.receipts.mkdir(parents=True, exist_ok=True)
    executable = args.codex_executable.resolve(strict=True)
    if not executable.is_file() or (os.name == 'nt' and executable.suffix.lower() != '.exe'):
        parser.error('codex-executable must be a native executable file')
    run_id = uuid.uuid4().hex
    output = args.receipts / f'{run_id}.jsonl'
    errors = args.receipts / f'{run_id}.stderr.log'
    with tempfile.TemporaryDirectory(prefix='codex-openrouter-') as home:
        # An isolated CODEX_HOME does not inherit the user's Windows sandbox
        # implementation. Without it, workspace-write can become read-only.
        config = CONFIG + ('\n[windows]\nsandbox = "elevated"\n' if os.name == 'nt' else '')
        Path(home, 'config.toml').write_text(config, encoding='utf-8')
        env = os.environ.copy()
        env['CODEX_HOME'] = home
        command = [str(executable), 'exec', '--json', '--ephemeral', '--cd', str(workdir),
                   '--sandbox', args.sandbox, '--model', args.model,
                   '-c', 'model_provider="openrouter"',
                   '-c', 'model_providers.openrouter.base_url="https://openrouter.ai/api/v1"',
                   '-c', 'model_providers.openrouter.env_key="OPENROUTER_API_KEY"',
                   '-c', 'model_providers.openrouter.wire_api="responses"',
                   '-c', 'model_providers.openrouter.requires_openai_auth=false',
                   '-c', 'model_providers.openrouter.request_max_retries=4',
                   '-c', 'model_providers.openrouter.stream_max_retries=5',
                   '-c', 'shell_environment_policy.exclude=["OPENROUTER_API_KEY"]']
        if args.disable_plugins:
            command += ['-c', 'features.plugins=false']
        command.append('-')
        with output.open('w', encoding='utf-8') as out, errors.open('w', encoding='utf-8') as err:
            try:
                exit_code = run_worker(command, input=assignment, text=True, stdout=out, stderr=err,
                                       env=env, check=False, timeout=None).returncode
            except subprocess.TimeoutExpired:
                print(json.dumps({'run_id': run_id, 'exit_code': None, 'turn_completed': False,
                                  'error': 'timeout', 'jsonl': str(output), 'stderr': str(errors)}))
                return 1
            except ProcessTreeCleanupError:
                print(json.dumps({'run_id': run_id, 'exit_code': None, 'turn_completed': False,
                                  'error': 'process_tree_cleanup_unverified', 'jsonl': str(output), 'stderr': str(errors)}))
                return 1
            except OSError as exc:
                print(f'CLI launch failed: {type(exc).__name__}', file=sys.stderr)
                return 1
    completed = False
    failed = False
    has_final_message = False
    for line in output.read_text(encoding='utf-8').splitlines():
        try:
            event = json.loads(line)
            completed |= event.get('type') == 'turn.completed'
            failed |= event.get('type') == 'turn.failed' or (
                event.get('type') == 'error'
                and not str(event.get('message', '')).startswith('Reconnecting... ')
            )
            item = event.get('item') or {}
            has_final_message |= event.get('type') == 'item.completed' and item.get('type') == 'agent_message'
            failed |= event.get('type') == 'item.completed' and item.get('type') == 'file_change' and item.get('status') == 'failed'
        except (ValueError, AttributeError):
            failed = True
    print(json.dumps({'run_id': run_id, 'exit_code': exit_code,
                      'turn_completed': completed, 'has_final_message': has_final_message,
                      'failed_event': failed, 'jsonl': str(output), 'stderr': str(errors)}))
    return 0 if exit_code == 0 and completed and has_final_message and not failed else 1


if __name__ == '__main__':
    sys.exit(main())
