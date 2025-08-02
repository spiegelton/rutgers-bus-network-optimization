# backend/verify_progress.py

import requests

def main():
    buses = requests.get("http://localhost:8000/buses").json()

    routes = {}
    for bus in buses:
        r = bus["route"].replace(" Route", "")
        if r not in routes:
            routes[r] = []
        routes[r].append((bus["name"], round(bus["progress"] or 0, 4), bus.get("isBunched", False)))

    for route, items in routes.items():
        print(f"\nRoute: {route}")
        for name, progress, bunched in sorted(items, key=lambda x: x[1]):
            tag = "Bunched" if bunched else ""
            print(f"  Bus #{name}: {progress:.3f} {tag}")

if __name__ == "__main__":
    main()
