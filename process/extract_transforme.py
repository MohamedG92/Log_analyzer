import re
import logging

log = logging.getLogger('process')

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# "May 24 01:14:12 ns sshd[1351821]: <message>"
patern = re.compile(r'^(\w{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+\S+\s+sshd\[\d+\]:\s(.+)$')
# "Failed password for root from 1.2.3.4 port 22 ssh2"
# "Failed password for invalid user admin from 1.2.3.4 port 22 ssh2"
failed_patern = re.compile(r'Failed \w+ for (?:invalid user )?(\S*) from (\d+\.\d+\.\d+\.\d+)')
# "Accepted password for adminesisa from 10.10.33.81 port 59176 ssh2"
success_patern = re.compile(r'Accepted \w+ for (\S+) from (\d+\.\d+\.\d+\.\d+)')
# "Invalid user admin from 1.2.3.4 port 22" -> the username does not exist on the server
invalid_patern = re.compile(r'Invalid user (\S*)\s+from (\d+\.\d+\.\d+\.\d+)')
# "message repeated 4 times: [ Failed password for root from ...]"
repeated_patern = re.compile(r'message repeated (\d+) times')


def extract_from_row(row):
    match = re.search(patern, row)
    if not match:
        return None
    month, day, time, message = match.groups()

    if month not in MONTHS:
        log.warning(f'unknown month "{month}", line ignored : {row[:100]}')
        return None

    status = None
    found = re.search(failed_patern, message)
    if found:
        status = 'failed'
    else:
        found = re.search(success_patern, message)
        if found:
            status = 'success'
        else:
            found = re.search(invalid_patern, message)
            if found:
                status = 'invalid'
    if status is None:
        return None

    count = 1
    repeated = re.search(repeated_patern, message)
    if repeated:
        count = int(repeated.group(1))

    return {
        'month': month,
        'day': int(day),
        'time': time,
        'date': f'{month} {int(day):02d}',
        'status': status,
        'user': found.group(1) or '(empty)',
        'ip': found.group(2),
        'count': count,
    }


def extract_all(rows):
    events = []
    for row in rows:
        event = extract_from_row(row)
        if event:
            events.append(event)
    if rows and not events:
        log.warning('no ssh login attempt found, are these really auth.log files ?')
    log.info(f'{len(rows)} lines -> {len(events)} ssh events')
    return events


def date_key(date):
    month, day = date.split()
    return (MONTHS.index(month), int(day))


def add(counter, key, n=1):
    counter[key] = counter.get(key, 0) + n


def top(counter, n=10):
    return sorted(counter.items(), key=lambda item: item[1], reverse=True)[:n]


def summarize(events, locations):
    summary = {
        'failed': 0, 'success': 0, 'invalid': 0,
        'per_day': {}, 'per_ip': {}, 'per_country': {},
        'success_users': {},   # who managed to log in
        'failed_users': {},    # usernames tried with a wrong password
        'invalid_users': {},   # usernames that don't exist on the server
    }
    not_located = set()
    for e in events:
        summary[e['status']] += e['count']
        if e['status'] == 'failed':
            add(summary['per_day'], e['date'], e['count'])
            add(summary['per_ip'], e['ip'], e['count'])
            add(summary['failed_users'], e['user'], e['count'])
            location = locations.get(e['ip'])
            if location is None:
                not_located.add(e['ip'])
                country = 'Unknown'
            else:
                country = location['country']
            add(summary['per_country'], country, e['count'])
        elif e['status'] == 'invalid':
            add(summary['invalid_users'], e['user'], e['count'])
        else:
            add(summary['success_users'], e['user'], e['count'])

    summary['attacking_ips'] = len(summary['per_ip'])
    if not_located:
        log.warning(f'{len(not_located)} ips have no country, counted as Unknown')
    if summary['success'] == 0:
        log.warning('no successful login found in the logs')
    return summary
