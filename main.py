import sys

from ingestion import raw
from process import extract_transforme
from process import geolocation
from storage import storage
from serving import graphs

if __name__ == "__main__":
    # first run, or "uv run main.py reload": logs -> MariaDB -> ipinfo
    if storage.is_empty() or 'reload' in sys.argv:
        events = extract_transforme.extract_all(raw.toRows('./data'))
        storage.save_events(events)
        storage.save_locations(geolocation.get_locations(storage.ips_to_locate()))

    graphs.print_report()
    graphs.show()
