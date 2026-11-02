import matplotlib.pyplot as plt

from process import extract_transforme
from process.extract_transforme import top


def barh(ax, items, title, color, xlabel='attempts'):
    labels = [label or '(empty)' for label, _ in items]
    values = [value for _, value in items]
    ax.barh(labels[::-1], values[::-1], color=color)
    ax.set_title(title)
    ax.set_xlabel(xlabel)


def show_graphs(summary, locations, top_ips):
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
    barh(axes[1][1], top(per_country, 15), f'Failed logins per country (top {top_ips} IPs)', '#5bc0de')

    # 6. top usernames that don't exist on the server
    barh(axes[1][2], top(summary['invalid_users'], 15), 'Top 15 invalid usernames', '#9b59b6')

    fig.tight_layout()
    plt.show()
