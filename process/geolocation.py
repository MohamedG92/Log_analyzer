import requests
from requests import Response
import concurrent.futures


def get_location(ip):
    try:
        response: Response = requests.get("https://ipinfo.io/" + ip + "/json", timeout=10)
    except requests.RequestException:
        return {'ip': ip, 'country': 'Unknown'}
    if response.status_code == 200:
        data = response.json()
        # private / reserved addresses (10.x, 127.x ...) come back as "bogon" with no country
        if data.get('bogon'):
            data['country'] = 'Private'
        data.setdefault('country', 'Unknown')
        return data
    return {'ip': ip, 'country': 'Unknown'}


def get_locations(ips, workers=20):
    # one request per IP, run in parallel so hundreds of IPs don't take minutes
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(get_location, ips)
        return dict(zip(ips, results))


if __name__ == "__main__":
    print(get_location("2.57.121.112"))
