import matplotlib.pyplot as plt

from ingestion import raw
from process import extract_transforme
from process import geolocation
from process.extract_transforme import top

# ipinfo.io without a token is rate-limited, so only the worst attackers are located
TOP_IPS = 100


def barh(ax, items, title, color, xlabel='attempts'):
    labels = [label or '(empty)' for label, _ in items]
    values = [value for _, value in items]
    ax.barh(labels[::-1], values[::-1], color=color)
    ax.set_title(title)
    ax.set_xlabel(xlabel)


def show_graphs(summary, locations):
    fig, axes = plt.subplots(2, 3, figsize=(20, 10))
    fig.suptitle('SSH auth.log analysis')

    # 1. failed password vs invalid user vs successful logins
    ax = axes[0][0]
    bars = ax.bar(['Failed password', 'Invalid user', 'Success'],
                  [summary['failed'], summary['invalid'], summary['success']],
                  color=['#d9534f', '#9b59b6', '#5cb85c'])
    ax.bar_label(bars)
    ax.set_title('Login attempts')
    ax.set_ylabel('attempts')

    # 2. failed logins per day
    ax = axes[0][1]
    days = sorted(summary['per_day'], key=extract_transforme.date_key)
    ax.plot(days, [summary['per_day'][d] for d in days], marker='o', color='#d9534f')
    ax.set_title('Failed logins per day')
    ax.set_ylabel('failed attempts')
    ax.tick_params(axis='x', rotation=60)

    # 3. top usernames tried with a wrong password
    barh(axes[0][2], top(summary['failed_users'], 15), 'Top 15 usernames tried (failed password)', '#e67e22')

    # 4. top attacking IPs (with their country)
    items = [(f"{ip} ({locations.get(ip, {}).get('country', '?')})", n) for ip, n in top(summary['per_ip'], 15)]
    barh(axes[1][0], items, 'Top 15 IPs by failed logins', '#f0ad4e')

    # 5. failed logins per country
    per_country = {}
    for ip, n in summary['per_ip'].items():
        if ip in locations:
            extract_transforme.add(per_country, locations[ip].get('country', 'Unknown'), n)
    barh(axes[1][1], top(per_country, 15), f'Failed logins per country (top {TOP_IPS} IPs)', '#5bc0de')

    # 6. top usernames that don't exist on the server
    barh(axes[1][2], top(summary['invalid_users'], 15), 'Top 15 invalid usernames', '#9b59b6')

    fig.tight_layout()
    plt.show()


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

    show_graphs(summary, locations)
