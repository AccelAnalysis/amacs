#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from amacs_io import DATASET_FILENAMES, DATASET_ORDER, ROOT, all_datasets


def flatten(value: Any) -> Any:
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description='Export AMACS logical datasets as review CSV files.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    datasets = all_datasets(ROOT)
    for name in DATASET_ORDER:
        records = datasets[name]
        if not records:
            continue
        columns: list[str] = []
        for record in records:
            for key in record:
                if key not in columns:
                    columns.append(key)
        target = output / DATASET_FILENAMES[name].replace('.jsonl', '.csv')
        with target.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for record in records:
                writer.writerow({key: flatten(record.get(key)) for key in columns})
        print(target)


if __name__ == '__main__':
    main()
