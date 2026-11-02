import requests
from requests import Response
import concurrent
def get_location(ip):
    response = requests.get("https://ipinfo.io/"+ip+"/json")
    if response.status_code == 200:
        print(response.json())



if __name__ == "__main__":
    print(get_location("2.57.121.112"))