"""Invoke one real local MCP tool with JSON-file arguments; no fake transport."""
import argparse
import asyncio
import json
from pathlib import Path

from mcp.client import Client


async def run(args):
    arguments = json.loads(args.arguments.read_text(encoding='utf-8-sig')) if args.arguments else {}
    async with Client('http://127.0.0.1:18892/mcp') as client:
        result = await client.call_tool(args.tool, arguments)
        if result.is_error:
            raise RuntimeError(str(result.content))
        value = result.structured_content or json.loads(result.content[0].text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    task = value.get('task', value)
    status = task.get('status', {})
    state = status.get('state') if isinstance(status, dict) else status
    print(json.dumps({'tool': args.tool, 'output': str(args.output),
                      'task_id': task.get('id', value.get('goal_id')), 'state': state}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', required=True)
    parser.add_argument('--arguments', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
