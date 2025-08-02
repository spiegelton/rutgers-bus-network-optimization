# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import passiogo
import numpy as np
from fastapi.responses import JSONResponse
import os
import json

from utils.progress import compute_progress, compute_progress_no_heading
from utils.bunching import is_bunched

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stop_routes = {
    10035: ["A Route", "EE Route", "H Route", "LX Route"],
    27767: ["A Route", "EE Route", "F Route", "H Route", "LX Route"],
    10038: ["A Route", "EE Route", "F Route", "H Route", "LX Route"],
    10034: ["A Route", "B Route", "B/L Loop", "C Route", "H Route", "REXB Route"],
    10041: ["A Route", "B Route", "B/L Loop"],
    10052: ["A Route", "B Route", "B/L Loop", "H Route"],
    10071: ["B Route", "LX Route", "REXL Route"],
    10029: ["B Route", "B/L Loop", "LX Route", "REXL Route"],
    10065: ["B Route", "B/L Loop", "LX Route"],
    10037: ["EE Route", "F Route", "REXB Route", "REXL Route"],
    10059: ["EE Route", "F Route", "REXB Route", "REXL Route"],
    10042: ["EE Route"],
    10026: ["EE Route"],
    10061: ["EE Route"],
    10036: ["EE Route", "F Route", "REXB Route", "REXL Route"],
    62662: ["EE Route"],
    10075: ["EE Route"],
    10039: ["C Route", "H Route", "REXB Route"],
    21050: ["C Route", "H Route", "REXB Route"],
    10060: ["A Route", "B/L Loop", "C Route", "H Route"],
    10089: ["A Route", "H Route"],
    153546: ["B/L Loop"],
    188704: ["B/L Loop"]
}

safe_stop_ids = {
    10035, 27767, 10034, 10041, 10052, 10029, 10065, 10037,
    10042, 10026, 10061, 10039, 21050, 10060, 10089, 153546
}

route_safe_stops_ordered = {
    "A": [10035, 27767, 10060, 10034, 10041, 10052, 10089],
    "B": [10034, 10041, 10052, 10029, 10065],
    "B/L Loop": [10060, 10034, 10041, 153546, 10029, 10065],
    "C": [10060, 10034, 10039, 21050],
    "EE": [10037, 10042, 10026, 10061, 10035, 27767],
    "F": [10037, 27767],
    "H": [10035, 27767, 10052, 10039, 21050, 10060],
    "LX": [10029, 10065, 10035, 27767],
    "REXB": [10037, 10034, 10039, 21050],
    "REXL": [10037, 10029]
}

route_polylines = {}
polyline_dir = "route_raw_polylines"

for fname in os.listdir(polyline_dir):
    if fname.endswith(".json"):
        route = fname.replace(".json", "")
        with open(os.path.join(polyline_dir, fname), "r") as f:
            route_polylines[route] = json.load(f)  # list of [lat, lon]


@app.get("/buses")
def get_live_buses():
    device_id = random.randint(10000000, 99999999)
    user_id = random.randint(10000, 99999)

    url = f"https://passiogo.com/mapGetData.php?getBuses=1&deviceId={device_id}&wTransloc=1&userId={user_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    }
    data = {
        "json": '{"s0":"1268","sA":1}'  # Rutgers system
    }

    response = requests.post(url, headers=headers, data=data)
    buses_data = response.json()
    raw_bus_list = []

    for bus_group in buses_data.get("buses", {}).values():
        for bus in bus_group:
            route_name = bus["route"].replace(" Route", "").replace("/", "_")
            polyline = route_polylines.get(route_name)
            lat, lon, course = float(bus["latitude"]), float(bus["longitude"]), float(bus["calculatedCourse"])

            progress = compute_progress(lat, lon, course, polyline) if polyline else None

            raw_bus_list.append({
                "id": bus["bus"],
                "name": bus["busName"],
                "route": bus["route"],
                "lat": float(bus["latitude"]),
                "lon": float(bus["longitude"]),
                "course": float(bus["calculatedCourse"]),
                "color": bus["color"],
                "paxLoad": bus["paxLoad"],
                "progress": progress
            })

    final_list = []
    buses_by_route = {}
    for b in raw_bus_list:
        route_short = b["route"].replace(" Route", "").replace("/", "_")
        buses_by_route.setdefault(route_short, []).append(b)

    for route, route_buses in buses_by_route.items():
        route_buses = [b for b in route_buses if b["progress"] is not None]
        sorted_buses = sorted(route_buses, key=lambda x: x["progress"])
        progress_vals = [b["progress"] for b in sorted_buses]
        bunched_indices = is_bunched(progress_vals)

        for i, b in enumerate(sorted_buses):
            b["isBunched"] = i in bunched_indices
            b["waitSuggestion"] = None

            if b["isBunched"]:
                route_key = b["route"].replace(" Route", "").replace("/", "_")
                bus_prog = b["progress"]
                safe_stop_ids_ordered = route_safe_stops_ordered.get(route_key, [])

                candidate_stops = []
                for stop_id in safe_stop_ids_ordered:
                    stop = stop_metadata.get(stop_id)
                    if not stop:
                        continue
                    stop_prog = compute_progress_no_heading(stop["lat"], stop["lon"], route_polylines[route_key])
                    dist = (stop_prog - bus_prog) % 1.0
                    candidate_stops.append((dist, stop))

                if candidate_stops:
                    candidate_stops.sort(key=lambda x: x[0])  # closest ahead stop by progress
                    next_stop = candidate_stops[0][1]

                    n = len(sorted_buses)
                    ideal_gap = 1.0 / n
                    next_i = (i + 1) % n
                    gap = (sorted_buses[next_i]["progress"] - b["progress"]) % 1.0
                    shortfall_ratio = max(0, (ideal_gap - gap) / ideal_gap)
                    wait_secs = min(120, max(30, int(shortfall_ratio * 120)))

                    b["waitSuggestion"] = {
                        "waitSeconds": wait_secs,
                        "atStopId": next_stop["id"],
                        "atStopName": next_stop["name"]
                    }

            final_list.append(b)

    return final_list


system = passiogo.getSystemFromID(1268)

stop_metadata = {}
for stop in system.getStops():
    stop_metadata[int(stop.id)] = {
        "id": int(stop.id),
        "name": stop.name,
        "lat": float(stop.latitude),
        "lon": float(stop.longitude),
        "routes": stop_routes.get(int(stop.id), [])
    }


@app.get("/stops")
def get_stops():
    stops = system.getStops()
    stops_list = []
    for stop in stops:
        s = stop.__dict__
        stop_id = s["id"]
        s["latitude"] = float(s["latitude"])
        s["longitude"] = float(s["longitude"])
        stops_list.append({
            "id": stop_id,
            "name": s["name"],
            "latitude": s["latitude"],
            "longitude": s["longitude"],
            "routes": stop_routes.get(int(stop_id), [])
        })
    return stops_list

@app.get("/eta/{stop_id}")
def get_eta(stop_id: str):
    device_id = random.randint(10000000, 99999999)

    url = f"https://passiogo.com/mapGetData.php?eta=3&deviceId={device_id}&stopIds={stop_id}"
    response = requests.get(url)
    data = response.json()

    eta_list = []
    if "ETAs" in data and stop_id in data["ETAs"]:
        for bus in data["ETAs"][stop_id]:
            eta_list.append({
                "route": bus["theStop"]["routeName"],
                "eta": bus["eta"]
            })

    return eta_list

@app.get("/route_polyline/{route_name}")
def get_route_polyline(route_name: str):
    path = os.path.join("route_raw_polylines", f"{route_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(status_code=404, content={"error": "Route not found"})
