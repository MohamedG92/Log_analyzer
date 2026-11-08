import logging
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from process.extract_transforme import top, date_key

log = logging.getLogger('serving')


def barh(ax, rows, title, color, xlabel='attempts'):
    # rows = list of (label, number), the biggest is shown on top
    if not rows:
        ax.text(0.5, 0.5, 'no data', ha='center', va='center')
        ax.set_title(title)
        ax.axis('off')
        log.warning(f'graph "{title}" is empty')
        return
    labels = [label for label, total in rows]
    values = [total for label, total in rows]
    # thin bars when there are only 1 or 2 rows, else one bar takes all the graph
    height = 0.8 if len(rows) > 2 else 0.3
    bars = ax.barh(labels[::-1], values[::-1], color=color, height=height)
    ax.bar_label(bars, fontsize=7, padding=2)
    # whole numbers only on the axis (no 0.2 login)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_title(title)
    ax.set_xlabel(xlabel)


def print_report(summary, locations):
    print(f"failed logins   : {summary['failed']}")
    print(f"invalid users   : {summary['invalid']}")
    print(f"success logins  : {summary['success']}")
    print(f"attacking IPs   : {summary['attacking_ips']}")

    print('\nfailed logins per country:')
    for country, total in top(summary['per_country'], 15):
        print(f"  {country:10} {total}")
    print('\nsuccessful logins per user:')
    for user, total in top(summary['success_users'], 15):
        print(f"  {user:16} {total}")
    print('\ntop invalid usernames:')
    for user, total in top(summary['invalid_users'], 10):
        print(f"  {user:16} {total}")
    print('\ntop usernames tried (failed password):')
    for user, total in top(summary['failed_users'], 10):
        print(f"  {user:16} {total}")
    print('\ntop attacking IPs:')
    for ip, total in top(summary['per_ip'], 10):
        location = locations.get(ip, {'country': '?', 'city': ''})
        line = f"  {ip:16} {total:6}  {location['country']}  {location['city']}"
        # the Windows console can't print every city name (e.g. Turkish letters)
        print(line.encode('ascii', 'replace').decode())


def show(summary, locations):
    fig, axes = plt.subplots(2, 3, figsize=(20, 10))
    fig.suptitle('SSH auth.log analysis')

    # ----- the 3 dashboards asked -----
    # 1. failed logins per country
    barh(axes[0][0], top(summary['per_country'], 15), 'Failed logins per country (top 15)', '#5bc0de')

    # 2. successful logins per user
    barh(axes[0][1], top(summary['success_users'], 15), 'Successful logins per user', '#5cb85c', 'logins')

    # 3. failed logins with a user that does not exist on the server
    barh(axes[0][2], top(summary['invalid_users'], 15), 'Top 15 invalid usernames', '#9b59b6')

    # ----- extra -----
    # 4. failed password vs invalid user vs successful logins
    ax = axes[1][0]
    bars = ax.bar(['Failed password', 'Invalid user', 'Success'],
                  [summary['failed'], summary['invalid'], summary['success']],
                  color=['#d9534f', '#9b59b6', '#5cb85c'])
    ax.bar_label(bars)
    ax.set_title('Login attempts')
    ax.set_ylabel('attempts')

    # 5. failed logins per day
    ax = axes[1][1]
    days = sorted(summary['per_day'].items(), key=lambda item: date_key(item[0]))
    ax.plot([day for day, total in days], [total for day, total in days], marker='o', color='#d9534f')
    ax.set_title('Failed logins per day')
    ax.set_ylabel('failed attempts')
    ax.tick_params(axis='x', rotation=60)

    # 6. top attacking IPs (with their country)
    ips = [(f"{ip} ({locations.get(ip, {'country': '?'})['country']})", total) for ip, total in top(summary['per_ip'], 15)]
    barh(axes[1][2], ips, 'Top 15 IPs by failed logins', '#f0ad4e')

    fig.tight_layout()
    plt.show()
