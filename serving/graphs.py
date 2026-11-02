import matplotlib.pyplot as plt

from storage import storage


def barh(ax, rows, key, title, color):
    labels = [row[key] or '(empty)' for row in rows]
    values = [int(row['total']) for row in rows]
    ax.barh(labels[::-1], values[::-1], color=color)
    ax.set_title(title)
    ax.set_xlabel('attempts')


def print_report():
    t = storage.totals()
    print(f"failed logins   : {t['failed']}")
    print(f"invalid users   : {t['invalid']}")
    print(f"success logins  : {t['success']}")
    print(f"attacking IPs   : {t['attacking_ips']}")
    for row in storage.successful_logins():
        print(f"success         : {row['log_date']}  {row['username']}  {row['ip']} ({row['country']})")

    print('\ntop usernames tried:')
    for row in storage.top_usernames(10):
        print(f"  {row['username']:16} {int(row['total'])}")
    print('\ntop invalid usernames:')
    for row in storage.top_invalid_usernames(10):
        print(f"  {row['username'] or '(empty)':16} {int(row['total'])}")
    print('\ntop attacking IPs:')
    for row in storage.top_ips(10):
        line = f"  {row['ip']:16} {int(row['total']):6}  {row['country']}  {row['city'] or ''}"
        # the Windows console can't print every city name (e.g. Turkish letters)
        print(line.encode('ascii', 'replace').decode())


def show():
    t = storage.totals()
    fig, axes = plt.subplots(2, 3, figsize=(20, 10))
    fig.suptitle('SSH auth.log analysis')

    # 1. failed password vs invalid user vs successful logins
    ax = axes[0][0]
    bars = ax.bar(['Failed password', 'Invalid user', 'Success'], [t['failed'], t['invalid'], t['success']],
                  color=['#d9534f', '#9b59b6', '#5cb85c'])
    ax.bar_label(bars)
    ax.set_title('Login attempts')
    ax.set_ylabel('attempts')

    # 2. failed logins per day
    ax = axes[0][1]
    days = storage.failed_per_day()
    ax.plot([d['day'].strftime('%b %d') for d in days], [int(d['total']) for d in days], marker='o', color='#d9534f')
    ax.set_title('Failed logins per day')
    ax.set_ylabel('failed attempts')
    ax.tick_params(axis='x', rotation=60)

    # 3. top usernames tried with a wrong password
    barh(axes[0][2], storage.top_usernames(), 'username', 'Top 15 usernames tried (failed password)', '#e67e22')

    # 4. top attacking IPs (with their country)
    ips = [{'label': f"{r['ip']} ({r['country'] or '?'})", 'total': r['total']} for r in storage.top_ips()]
    barh(axes[1][0], ips, 'label', 'Top 15 IPs by failed logins', '#f0ad4e')

    # 5. failed logins per country
    barh(axes[1][1], storage.failed_per_country(), 'country',
         f'Failed logins per country (top {storage.TOP_IPS_TO_LOCATE} IPs)', '#5bc0de')

    # 6. top usernames that don't exist on the server
    barh(axes[1][2], storage.top_invalid_usernames(), 'username', 'Top 15 invalid usernames', '#9b59b6')

    fig.tight_layout()
    plt.show()
