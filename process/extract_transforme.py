import re


MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# "May 24 01:14:12 ns sshd[1351821]: <message>"
patern = re.compile(r'^(\w{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+\S+\s+sshd\[\d+\]:\s(.+)$')
# "Failed password for root from 1.2.3.4 port 22 ssh2"
# "Failed password for invalid user admin from 1.2.3.4 port 22 ssh2"
failed_patern = re.compile(r'Failed \w+ for (?:invalid user )?(\S*) from (\d+\.\d+\.\d+\.\d+)')
# "Accepted password for adminesisa from 10.10.33.81 port 59176 ssh2"
success_patern = re.compile(r'Accepted \w+ for (\S+) from (\d+\.\d+\.\d+\.\d+)')
# "message repeated 4 times: [ Failed password for root from ...]"
repeated_patern = re.compile(r'message repeated (\d+) times')


def extract_from_row(row):
    match = re.search(patern, row)
    if not match:
        return None
    month, day, time, message = match.groups()

    status = None
    found = re.search(failed_patern, message)
    if found:
        status = 'failed'
    else:
        found = re.search(success_patern, message)
        if found:
            status = 'success'
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
    return events


def date_key(date):
    month, day = date.split()
    return (MONTHS.index(month), int(day))


def summarize(events):
    summary = {'failed': 0, 'success': 0, 'per_day': {}, 'per_ip': {}, 'success_ips': {}}
    for e in events:
        summary[e['status']] += e['count']
        if e['status'] == 'failed':
            summary['per_day'][e['date']] = summary['per_day'].get(e['date'], 0) + e['count']
            summary['per_ip'][e['ip']] = summary['per_ip'].get(e['ip'], 0) + e['count']
        else:
            summary['success_ips'][e['ip']] = summary['success_ips'].get(e['ip'], 0) + e['count']
    return summary
