#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from amacs_io import DATASET_FILENAMES, DATASET_ORDER, ROOT, all_datasets, write_jsonl


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description='Build an immutable AMACS release directory.')
    parser.add_argument('--output', required=True)
    parser.add_argument('--source-commit', default='UNCOMMITTED')
    args = parser.parse_args()

    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    target = Path(args.output) / version
    if target.exists():
        shutil.rmtree(target)
    source_target = target / 'source'
    schema_target = target / 'schemas'
    seed_target = target / 'source-seeds'
    source_target.mkdir(parents=True)
    schema_target.mkdir(parents=True)
    seed_target.mkdir(parents=True)

    datasets = all_datasets(ROOT)
    for name in DATASET_ORDER:
        write_jsonl(source_target / DATASET_FILENAMES[name], datasets[name])

    for schema in sorted((ROOT / 'schemas').glob('*.json')):
        shutil.copy2(schema, schema_target / schema.name)
    shutil.copytree(ROOT / 'source' / 'domain-seeds', seed_target / 'domain-seeds')
    shutil.copy2(ROOT / 'source' / 'alias-seed.json', seed_target / 'alias-seed.json')

    counts = {DATASET_FILENAMES[name].removesuffix('.jsonl'): len(datasets[name]) for name in DATASET_ORDER}
    manifest = {
        'name': 'Accel Market Activity and Capability Standard',
        'version': version,
        'status': 'development',
        'released_at': '2026-08-03',
        'source_commit': args.source_commit,
        'record_counts': counts,
    }
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

    checksums: list[str] = []
    for path in sorted(target.rglob('*')):
        if path.is_file() and path.name != 'SHA256SUMS':
            checksums.append(f'{sha256(path)}  {path.relative_to(target).as_posix()}')
    (target / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n', encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()
