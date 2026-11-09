import os
import logging
import requests
from requests import Response

log = logging.getLogger('process')

# optional: set IPINFO_TOKEN in the terminal to lift ipinfo's free rate limit (no .env file needed)
TOKEN = os.environ.get('IPINFO_TOKEN')
# returned by get_location when ipinfo answers 429 (too many requests)
LIMIT = 'limit'


def get_location(ip):
    # returns {'country', 'city'} or None if ipinfo did not answer (the ip will be retried next run)
    params = {'token': TOKEN} if TOKEN else None
    try:
        response: Response = requests.get("https://ipinfo.io/" + ip + "/json", params=params, timeout=10)
    except requests.Timeout:
        log.error(f'ipinfo {ip} : timeout')
        return None
    except requests.ConnectionError:
        log.error(f'ipinfo {ip} : no connection (internet down ?)')
        return None
    except requests.RequestException as e:
        log.error(f'ipinfo {ip} : {e}')
        return None

    if response.status_code == 429:
        return LIMIT
    if response.status_code != 200:
        log.error(f'ipinfo {ip} : http {response.status_code}')
        return None

    try:
        data = response.json()
    except ValueError:
        log.error(f'ipinfo {ip} : the answer is not json')
        return None

    # private / reserved addresses (10.x, 127.x ...) come back as "bogon" with no country
    if data.get('bogon'):
        return {'country': 'Private', 'city': ''}
    return {'country': data.get('country', 'Unknown'), 'city': data.get('city', '')}


def get_locations(ips, cache):
    # ips must be sorted from the biggest attacker to the smallest :
    # if ipinfo blocks us, at least the important ones are located
    # only the ips that are not already in the cache (locations.csv) are sent to ipinfo
    new_ips = [ip for ip in ips if ip not in cache]
    log.info(f'{len(ips)} ips, {len(new_ips)} not in the cache -> ipinfo')

    errors = 0
    # one request per IP, one after the other
    for i, ip in enumerate(new_ips):
        location = get_location(ip)
        if location == LIMIT:
            # no need to send the other requests, they will all get 429
            left = len(new_ips) - i
            log.error(f'ipinfo limit reached (429), {left + errors} ips not located, '
                      f'set IPINFO_TOKEN or run again later')
            return cache
        if location is None:
            errors += 1
        else:
            cache[ip] = location

    if errors:
        log.warning(f'{errors} ips could not be located, they will be retried next run')
    return cache


if __name__ == "__main__":
    print(get_location("2.57.121.112"))
