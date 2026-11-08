import os
import csv
import logging

log = logging.getLogger('storage')

# no database : everything is kept in csv files next to this file
FOLDER = os.path.dirname(__file__)
EVENTS_FILE = os.path.join(FOLDER, 'events.csv')
LOCATIONS_FILE = os.path.join(FOLDER, 'locations.csv')

EVENT_COLUMNS = ['month', 'day', 'time', 'date', 'status', 'user', 'ip', 'count']
LOCATION_COLUMNS = ['ip', 'country', 'city']


def is_empty():
    return not os.path.exists(EVENTS_FILE)


# ---------- events (one line per login attempt) ----------

def save_events(events):
    # the file is rewritten each time, so loading twice never doubles the data
    try:
        with open(EVENTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=EVENT_COLUMNS)
            writer.writeheader()
            writer.writerows(events)
    except PermissionError:
        log.error(f'no permission to write {EVENTS_FILE} (open in excel ?)')
        return 0
    except OSError as e:
        log.error(f'cannot write {EVENTS_FILE} : {e}')
        return 0
    log.info(f'{len(events)} events saved in {EVENTS_FILE}')
    return len(events)


def load_events():
    events = []
    try:
        with open(EVENTS_FILE, 'r', newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                row['day'] = int(row['day'])
                row['count'] = int(row['count'])
                events.append(row)
    except FileNotFoundError:
        log.error(f'{EVENTS_FILE} not found, run "uv run main.py reload"')
        return []
    except (OSError, KeyError, ValueError) as e:
        log.error(f'{EVENTS_FILE} is broken ({e}), run "uv run main.py reload"')
        return []
    log.info(f'{len(events)} events loaded from {EVENTS_FILE}')
    return events


# ---------- locations (cache of ipinfo, an ip is located only once) ----------

def load_locations():
    locations = {}
    if not os.path.exists(LOCATIONS_FILE):
        log.info(f'{LOCATIONS_FILE} not found, starting with an empty cache')
        return locations
    try:
        with open(LOCATIONS_FILE, 'r', newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                locations[row['ip']] = {'country': row['country'], 'city': row['city']}
    except (OSError, KeyError) as e:
        log.error(f'{LOCATIONS_FILE} is broken ({e}), the ips will be located again')
        return {}
    log.info(f'{len(locations)} locations loaded from the cache')
    return locations


def save_locations(locations):
    try:
        with open(LOCATIONS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LOCATION_COLUMNS)
            writer.writeheader()
            for ip, location in locations.items():
                writer.writerow({'ip': ip, 'country': location['country'], 'city': location['city']})
    except PermissionError:
        log.error(f'no permission to write {LOCATIONS_FILE} (open in excel ?)')
        return
    except OSError as e:
        log.error(f'cannot write {LOCATIONS_FILE} : {e}')
        return
    log.info(f'{len(locations)} locations saved in {LOCATIONS_FILE}')
