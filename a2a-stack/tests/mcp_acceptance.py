"""Explicit live MCP facade tests. Registers only bounded local check fixtures."""
import argparse
import asyncio
import importlib.util
import json
import sys
import time
import uuid
from pathlib import Path

from mcp.client import Client
from mcp_roundtrip import payload

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'tmp' / 'a2a-stack'
spec = importlib.util.spec_from_file_location('lifecycle', ROOT / 'a2a-stack/runtime/runner.py')
lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lifecycle)


async def wait_task(client, task_id, states, seconds=10):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        task = payload(await client.call_tool('get_task', {'task_id': task_id}))
        if task['status']['state'] in states:
            return task
        await asyncio.sleep(.1)
    raise TimeoutError(f'Task {task_id} not in {states}')


async def main(output):
    tag = 'mcp-qa-' + uuid.uuid4().hex[:10]
    jobs = STATE / 'jobs'
    jobs.mkdir(parents=True, exist_ok=True)
    quick = jobs / (tag + '-quick.json')
    slow = jobs / (tag + '-slow.json')
    quick.write_text(json.dumps({'mode': 'check', 'command': [sys.executable, '-c', "print('mcp-artifact-ok')"], 'timeout_seconds': 5}))
    slow.write_text(json.dumps({'mode': 'check', 'command': [sys.executable, '-c', 'import time;time.sleep(60)'], 'timeout_seconds': 30}))
    active = None
    cases = []
    async with Client('http://127.0.0.1:18892/mcp') as client:
        try:
            tool_names = {tool.name for tool in (await client.list_tools()).tools}
            assert tool_names == {'discover_agent', 'submit_job', 'get_task', 'cancel_task', 'list_tasks',
                                  'list_templates', 'create_stack', 'list_stacks', 'get_stack', 'create_assignment',
                                  'list_goal_checks', 'set_goal', 'list_goals', 'get_goal_report',
                                  'stop_goal', 'resume_goal', 'freeze_goal_candidate'}, tool_names
            card = payload(await client.call_tool('discover_agent', {}))
            assert card['agent_card']['supportedInterfaces'][0]['protocolVersion'] == '1.0'
            cases.append('tool discovery and actual A2A card')
            submitted = payload(await client.call_tool('submit_job', {'job_name': quick.stem}))
            task = await wait_task(client, submitted['task']['id'], {'TASK_STATE_COMPLETED'})
            assert any(p.get('text') == 'mcp-artifact-ok' for a in task['artifacts'] for p in a['parts'])
            cases.append('submit, poll and actual artifact')
            listing = payload(await client.call_tool('list_tasks', {}))
            assert task['id'] in [item['id'] for item in listing['tasks']]
            cases.append('list returns real task')
            invalid = await client.call_tool('get_task', {'task_id': str(uuid.uuid4())})
            assert invalid.is_error, 'Unknown task reported as success'
            empty = await client.call_tool('submit_job', {'job_name': ''})
            assert empty.is_error, 'Empty job reported as success'
            cases.append('errors remain MCP errors')
            submitted = payload(await client.call_tool('submit_job', {'job_name': slow.stem}))
            active = submitted['task']['id']
            await wait_task(client, active, {'TASK_STATE_WORKING'})
            process_file = STATE / 'tasks' / active / 'process.json'
            for _ in range(50):
                if process_file.exists():
                    break
                await asyncio.sleep(.1)
            process = json.loads(process_file.read_text())
            assert lifecycle.process_token(process['pid']) == process['process_token']
            payload(await client.call_tool('cancel_task', {'task_id': active}))
            await wait_task(client, active, {'TASK_STATE_CANCELED'})
            assert lifecycle.process_token(process['pid']) != process['process_token'], 'Canceled process still live'
            active = None
            cases.append('MCP cancellation and actual process exit')
        finally:
            if active:
                await client.call_tool('cancel_task', {'task_id': active})
            quick.unlink(missing_ok=True)
            slow.unlink(missing_ok=True)
    report = {'verdict': 'READY', 'scope': 'running Docker MCP facade to real host A2A service', 'cases': cases}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.output))
