import os
import gzip


def read_file(path):
    # rotated logs (auth.log.3.gz ...) are compressed, the others are plain text
    if path.endswith('.gz'):
        with gzip.open(path, 'rt', encoding='utf-8', errors='replace') as f:
            return f.read().splitlines()
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read().splitlines()


def toRows(folder):
    rows = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and name.startswith('auth.log'):
            rows.extend(read_file(path))
    return rows
