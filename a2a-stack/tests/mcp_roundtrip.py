"""Explicit live MCP -> A2A job test; never runs during unit test discovery."""
import argparse
import asyncio
import json
import time
from pathlib import Path

from mcp.client import Client


def payload(result):
    if result.is_error:
        raise RuntimeError(str(result.content))
    return result.structured_content or json.loads(result.content[0].text)


async def run(job, timeout, output, expected):
    async with Client('http://127.0.0.1:18892/mcp') as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        required = {'discover_agent', 'submit_job', 'get_task', 'cancel_task', 'list_tasks'}
        assert required <= names, names
        control = {'list_templates', 'create_stack', 'list_stacks', 'get_stack', 'create_assignment'}
        assert control <= names, names
        card = payload(await client.call_tool('discover_agent', {}))
        submitted = payload(await client.call_tool('submit_job', {'job_name': job}))
        task = submitted['task']
        task_id = task['id']
        print(json.dumps({'submitted': task_id, 'job': job}), flush=True)
        end = time.monotonic() + timeout
        while True:
            task = payload(await client.call_tool('get_task', {'task_id': task_id}))
            state = task['status']['state']
            if state not in ('TASK_STATE_SUBMITTED', 'TASK_STATE_WORKING'):
                break
            if time.monotonic() >= end:
                raise TimeoutError(f'Task still {state}; query original ID {task_id}, do not resubmit')
            await asyncio.sleep(1)
        receipt = {'tools': sorted(names), 'agent': card['agent_card']['name'],
                   'job': job, 'task_id': task_id, 'state': state,
                   'artifacts': task.get('artifacts', []), 'status': task['status']}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(receipt, ensure_ascii=True), flush=True)
        assert state == 'TASK_STATE_COMPLETED', receipt
        assert task.get('artifacts'), 'No actual artifact returned'
        artifact_text = '\n'.join(part.get('text', '') for artifact in task['artifacts'] for part in artifact.get('parts', []))
        for value in expected:
            assert value in artifact_text, f'Job completed, but required business evidence absent: {value}'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', required=True, help='Existing trusted registered job, not arbitrary code')
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-text', action='append', default=[])
    args = parser.parse_args()
    asyncio.run(run(args.job, args.timeout, args.output, args.expect_text))
