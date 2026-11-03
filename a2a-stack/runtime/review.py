"""Bind independent acceptance to the exact reviewed files, including untracked ones."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("A2A_WORKSPACE", Path(__file__).resolve().parents[2])).resolve()


def candidate(paths):
    files = {}
    for name in sorted(set(paths)):
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f'Not a project file: {name}')
        files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not files:
        raise ValueError('An acceptance candidate must contain files')
    identity = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {'candidate': identity, 'files': files}


def accept(manifest, review):
    current = candidate(manifest['files'])
    if current != manifest:
        raise ValueError('STALE: reviewed files changed; freeze and re-review')
    if review.get('candidate') != manifest['candidate']:
        raise ValueError('Review refers to another candidate')
    if not review.get('reviewer') or review.get('reviewer') == review.get('author'):
        raise ValueError('Independent reviewer identity is required')
    if review.get('verdict') != 'READY' or not review.get('evidence'):
        raise ValueError('Only READY with evidence can be accepted')
    return {'accepted': True, 'candidate': current['candidate'], 'reviewer': review['reviewer']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    freeze = sub.add_parser('freeze')
    freeze.add_argument('--files', nargs='+', required=True)
    freeze.add_argument('--output', type=Path, required=True)
    verify = sub.add_parser('accept')
    verify.add_argument('--manifest', type=Path, required=True)
    verify.add_argument('--review', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == 'freeze':
            result = candidate(args.files)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
        else:
            result = accept(json.loads(args.manifest.read_text(encoding='utf-8')),
                            json.loads(args.review.read_text(encoding='utf-8')))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
