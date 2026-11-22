# Log Analyzer

This Python project analyses the SSH logs of a Linux server (`auth.log`) to see who is trying to log in, from which country and with which usernames.

The program reads the files in the `data` folder (even `.gz` ones), uses regular expressions to keep failed passwords, invalid users and successful logins, then looks up the country of each IP with ipinfo.io. The results are saved in `storage/events.csv` and `storage/locations.csv`, and the matplotlib dashboard shows failed attempts by country, successful logins by user and attempts with an invalid user.

To install it you need Python 3.14 and uv, then run `uv sync`. To start it, run `uv run main.py`, or `uv run main.py reload` if you change the files in `data`. It only uses matplotlib and requests. Without a token ipinfo blocks quickly, so you can set one with `$env:IPINFO_TOKEN = "your_token"`. IPs that were already looked up stay in `locations.csv` and are not requested again.

There is no database because two CSV files are enough for a few thousand lines. Each module has its own log file in the `logs` folder, so you know where to look when something goes wrong.

In our logs we found 16,361 failed passwords coming from 1,853 IPs, mostly targeting root, and 3,166 attempts with a user that doesn't exist. The only successful login comes from the local network (adminesisa from 10.10.33.81), so nobody from outside got in.
