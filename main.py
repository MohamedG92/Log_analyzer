from ingestion import raw
from process import extract_transforme
from process import geolocation
from process.extract_transforme import top
from serving import graphs

# ipinfo.io without a token is rate-limited, so only the worst attackers are located
TOP_IPS = 100


if __name__ == "__main__":
    rows = raw.toRows('./data')
    events = extract_transforme.extract_all(rows)
    summary = extract_transforme.summarize(events)

    print(f'lines read      : {len(rows)}')
    print(f'failed logins   : {summary["failed"]}')
    print(f'invalid users   : {summary["invalid"]} ({len(summary["invalid_users"])} different names)')
    print(f'success logins  : {summary["success"]}')
    print(f'attacking IPs   : {len(summary["per_ip"])}')
    for ip, n in summary['success_ips'].items():
        print(f'success from    : {ip} ({n})')

    print('\ntop usernames tried:')
    for user, n in top(summary['failed_users']):
        print(f'  {user:16} {n}')
    print('\ntop invalid usernames:')
    for user, n in top(summary['invalid_users']):
        print(f'  {user or "(empty)":16} {n}')

    print('\ntop attacking IPs:')
    top_ips = [ip for ip, _ in top(summary['per_ip'], TOP_IPS)]
    locations = geolocation.get_locations(top_ips + list(summary['success_ips']))
    for ip in top_ips[:10]:
        loc = locations[ip]
        line = f'  {ip:16} {summary["per_ip"][ip]:6}  {loc.get("country")}  {loc.get("city", "")}  {loc.get("org", "")}'
        # the Windows console can't print every city name (e.g. Turkish letters)
        print(line.encode('ascii', 'replace').decode())

    graphs.show_graphs(summary, locations, TOP_IPS)
