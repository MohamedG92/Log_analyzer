import os
import gzip
import logging

log = logging.getLogger('ingestion')


def read_file(path):
    # rotated logs (auth.log.3.gz ...) are compressed, the others are plain text
    try:
        if path.endswith('.gz'):
            with gzip.open(path, 'rt', encoding='utf-8', errors='replace') as f:
                lines = f.read().splitlines()
        else:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.read().splitlines()
    except PermissionError:
        log.error(f'no permission to read {path}')
        return []
    except (gzip.BadGzipFile, EOFError):
        # .gz file cut in the middle or not really compressed
        log.error(f'{path} is not a valid .gz file (corrupted ?)')
        return []
    except OSError as e:
        log.error(f'cannot read {path} : {e}')
        return []

    if not lines:
        log.warning(f'{path} is empty')
    else:
        log.info(f'{path} : {len(lines)} lines')
    return lines


def toRows(folder):
    if not os.path.isdir(folder):
        log.error(f'the folder {folder} does not exist')
        return []

    rows = []
    files = 0
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and name.startswith('auth.log'):
            rows.extend(read_file(path))
            files += 1

    if files == 0:
        log.error(f'no auth.log file in {folder}')
    log.info(f'{files} files read, {len(rows)} lines in total')
    return rows
