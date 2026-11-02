import matplotlib.pyplot as plt

from ingestion import raw
from process import extract_transforme
from process import geolocation

# ipinfo.io without a token is rate-limited, so only the worst attackers are located
TOP_IPS = 100


def show_graphs(summary, locations):
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('SSH auth.log analysis')

    # 1. failed vs successful logins
    ax = axes[0][0]
    bars = ax.bar(['Failed', 'Success'], [summary['failed'], summary['success']], color=['#d9534f', '#5cb85c'])
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

    # 3. top attacking IPs (with their country)
    ax = axes[1][0]
    top = sorted(summary['per_ip'].items(), key=lambda x: x[1], reverse=True)[:15]
    labels = [f"{ip} ({locations.get(ip, {}).get('country', '?')})" for ip, _ in top]
    ax.barh(labels[::-1], [n for _, n in top][::-1], color='#f0ad4e')
    ax.set_title('Top 15 IPs by failed logins')
    ax.set_xlabel('failed attempts')

    # 4. failed logins per country
    ax = axes[1][1]
    per_country = {}
    for ip, n in summary['per_ip'].items():
        if ip in locations:
            country = locations[ip].get('country', 'Unknown')
            per_country[country] = per_country.get(country, 0) + n
    countries = sorted(per_country.items(), key=lambda x: x[1], reverse=True)[:15]
    ax.barh([c for c, _ in countries][::-1], [n for _, n in countries][::-1], color='#5bc0de')
    ax.set_title(f'Failed logins per country (top {TOP_IPS} IPs)')
    ax.set_xlabel('failed attempts')

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    rows = raw.toRows('./data')
    events = extract_transforme.extract_all(rows)
    summary = extract_transforme.summarize(events)

    print(f'lines read      : {len(rows)}')
    print(f'failed logins   : {summary["failed"]}')
    print(f'success logins  : {summary["success"]}')
    print(f'attacking IPs   : {len(summary["per_ip"])}')
    for ip, n in summary['success_ips'].items():
        print(f'success from    : {ip} ({n})')

    top_ips = sorted(summary['per_ip'], key=summary['per_ip'].get, reverse=True)[:TOP_IPS]
    locations = geolocation.get_locations(top_ips + list(summary['success_ips']))
    for ip in top_ips[:10]:
        loc = locations[ip]
        line = f'{ip:16} {summary["per_ip"][ip]:6}  {loc.get("country")}  {loc.get("city", "")}  {loc.get("org", "")}'
        # the Windows console can't print every city name (e.g. Turkish letters)
        print(line.encode('ascii', 'replace').decode())

    show_graphs(summary, locations)
