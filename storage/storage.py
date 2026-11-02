import os
import pymysql
from datetime import datetime


def load_env(path=os.path.join(os.path.dirname(__file__), '..', '.env')):
    # reads KEY=value lines from the project's .env (no extra library needed)
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())


load_env()

# MariaDB server (not XAMPP) - the login is in .env
SETTINGS = dict(host=os.environ.get('DB_HOST', 'localhost'),
                port=int(os.environ.get('DB_PORT', 3306)),
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD', ''),
                charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
DATABASE = os.environ.get('DB_NAME', 'log_analyser')
TABLE = 't_log'
YEAR = 2026               # syslog lines have no year
TOP_IPS_TO_LOCATE = 100   # ipinfo without a token is rate-limited

_connection = None


def get_connection():
    # connect only when needed, and create the database the first time
    global _connection
    if _connection is None:
        try:
            server = pymysql.connect(**SETTINGS)
        except pymysql.err.OperationalError as e:
            raise SystemExit(f"Cannot reach MariaDB on {SETTINGS['host']}:{SETTINGS['port']} ({e}). Start the MariaDB server first.")
        with server.cursor() as cursor:
            cursor.execute('CREATE DATABASE IF NOT EXISTS ' + DATABASE + ' CHARACTER SET utf8mb4')
        server.close()
        _connection = pymysql.connect(database=DATABASE, **SETTINGS)
    return _connection


def query(sql, params=None):
    with get_connection().cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


# ---------- write ----------

def create_table():
    # rebuilt on every load, so loading twice never doubles the data
    with get_connection().cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS ' + TABLE)
        cursor.execute('CREATE TABLE ' + TABLE + ' ('
                       ' id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,'
                       ' log_date DATETIME NOT NULL,'
                       ' status VARCHAR(10) NOT NULL,'      # failed / invalid / success
                       ' username VARCHAR(100) COLLATE utf8mb4_bin,'  # case-sensitive: Admin != admin
                       ' ip VARCHAR(45),'
                       ' attempts INT NOT NULL DEFAULT 1,'  # "message repeated 4 times" = 4
                       ' country VARCHAR(10),'
                       ' city VARCHAR(100),'
                       ' INDEX (ip), INDEX (status))')
    get_connection().commit()


def save_events(events, batch=5000):
    create_table()
    values = [(datetime.strptime(f"{YEAR} {e['month']} {e['day']} {e['time']}", '%Y %b %d %H:%M:%S'),
               e['status'], e['user'], e['ip'], e['count']) for e in events]
    with get_connection().cursor() as cursor:
        for i in range(0, len(values), batch):
            cursor.executemany('INSERT INTO ' + TABLE + ' (log_date, status, username, ip, attempts)'
                               ' VALUES (%s, %s, %s, %s, %s)', values[i:i + batch])
    get_connection().commit()
    return len(values)


def ips_to_locate(n=TOP_IPS_TO_LOCATE):
    # the n IPs with the most failed passwords + every IP that logged in successfully
    ips = [r['ip'] for r in top_ips(n)]
    ips += [r['ip'] for r in successful_logins() if r['ip'] not in ips]
    return ips


def save_locations(locations):
    with get_connection().cursor() as cursor:
        cursor.executemany('UPDATE ' + TABLE + ' SET country = %s, city = %s WHERE ip = %s',
                           [(loc.get('country', 'Unknown')[:10], (loc.get('city') or '')[:100] or None, ip)
                            for ip, loc in locations.items()])
    get_connection().commit()


def is_empty():
    exists = query('SELECT COUNT(*) AS n FROM information_schema.tables'
                   ' WHERE table_schema = %s AND table_name = %s', (DATABASE, TABLE))[0]['n']
    return not exists or query('SELECT COUNT(*) AS n FROM ' + TABLE)[0]['n'] == 0


# ---------- read ----------

def totals():
    rows = query('SELECT status, SUM(attempts) AS total FROM ' + TABLE + ' GROUP BY status')
    result = {'failed': 0, 'invalid': 0, 'success': 0}
    result.update({r['status']: int(r['total']) for r in rows})
    result['attacking_ips'] = query("SELECT COUNT(DISTINCT ip) AS n FROM " + TABLE + " WHERE status = 'failed'")[0]['n']
    return result

def failed_per_day():
    return query("SELECT DATE(log_date) AS day, SUM(attempts) AS total FROM " + TABLE +
                 " WHERE status = 'failed' GROUP BY day ORDER BY day")

def top_ips(n=15):
    return query("SELECT ip, MAX(country) AS country, MAX(city) AS city, SUM(attempts) AS total FROM " + TABLE +
                 " WHERE status = 'failed' GROUP BY ip ORDER BY total DESC LIMIT %s", (n,))

def failed_per_country(n=15):
    return query("SELECT country, SUM(attempts) AS total FROM " + TABLE +
                 " WHERE status = 'failed' AND country IS NOT NULL GROUP BY country ORDER BY total DESC LIMIT %s", (n,))

def top_usernames(n=15):
    return query("SELECT username, SUM(attempts) AS total FROM " + TABLE +
                 " WHERE status = 'failed' GROUP BY username ORDER BY total DESC LIMIT %s", (n,))

def top_invalid_usernames(n=15):
    return query("SELECT username, SUM(attempts) AS total FROM " + TABLE +
                 " WHERE status = 'invalid' GROUP BY username ORDER BY total DESC LIMIT %s", (n,))

def successful_logins():
    return query("SELECT log_date, username, ip, country FROM " + TABLE +
                 " WHERE status = 'success' ORDER BY log_date")
