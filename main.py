import os
import sys
import logging

from ingestion import raw
from process import extract_transforme
from process import geolocation
from storage import storage
from serving import graphs

LOG_FOLDER = 'logs'
MODULES = ['main', 'ingestion', 'process', 'storage', 'serving']


def setup_logs():
    # one log file per module in logs/ (logs/ingestion.log, logs/process.log ...)
    # the console only shows the warnings and errors
    os.makedirs(LOG_FOLDER, exist_ok=True)
    format = logging.Formatter('%(asctime)s | %(levelname)-7s | %(name)s | %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(format)
    for module in MODULES:
        logger = logging.getLogger(module)
        logger.setLevel(logging.INFO)
        file = logging.FileHandler(os.path.join(LOG_FOLDER, module + '.log'), encoding='utf-8')
        file.setFormatter(format)
        logger.addHandler(file)
        logger.addHandler(console)


def run():
    log = logging.getLogger('main')
    log.info('start')

    # first run, or "uv run main.py reload": logs -> events.csv
    if storage.is_empty() or 'reload' in sys.argv:
        events = extract_transforme.extract_all(raw.toRows('./data'))
        if not events:
            log.error('no event found in ./data, nothing to analyse')
            sys.exit(1)
        storage.save_events(events)
    else:
        events = storage.load_events()
        if not events:
            sys.exit(1)

    # country of every ip, ipinfo is only called for the ips not in locations.csv
    # the ips with the most attempts first
    attempts = {}
    for e in events:
        attempts[e['ip']] = attempts.get(e['ip'], 0) + e['count']
    ips = sorted(attempts, key=lambda ip: attempts[ip], reverse=True)
    locations = geolocation.get_locations(ips, storage.load_locations())
    storage.save_locations(locations)

    summary = extract_transforme.summarize(events, locations)
    graphs.print_report(summary, locations)
    graphs.show(summary, locations)
    log.info('end')


if __name__ == "__main__":
    setup_logs()
    try:
        run()
    except KeyboardInterrupt:
        logging.getLogger('main').warning('stopped with ctrl+c')
    except Exception as e:
        # unexpected error : the full traceback goes in logs/main.log
        logging.getLogger('main').exception(f'unexpected error : {e}')
        sys.exit(1)
