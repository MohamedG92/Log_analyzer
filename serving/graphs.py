import logging
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from process.extract_transforme import top

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
    fig, axes = plt.subplots(1, 3, figsize=(20, 7))
    fig.suptitle('SSH auth.log analysis')

    # 1. failed logins per country
    barh(axes[0], top(summary['per_country'], 15), 'Failed logins per country (top 15)', '#5bc0de')

    # 2. successful logins per user
    barh(axes[1], top(summary['success_users'], 15), 'Successful logins per user', '#5cb85c', 'logins')

    # 3. failed logins with a user that does not exist on the server
    barh(axes[2], top(summary['invalid_users'], 15), 'Top 15 invalid usernames', '#9b59b6')

    fig.tight_layout()
    plt.show()
