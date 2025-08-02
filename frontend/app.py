import streamlit as st
import requests
from streamlit_folium import st_folium
import folium
from folium.features import DivIcon

st.set_page_config(layout="wide", page_title="Rutgers Bus Network")
st.title("🚌 Rutgers Buses + Stops (Live)")

API_BASE = "http://localhost:8000"

# -- Cache stops (static)
@st.cache_data
def fetch_stops():
    return requests.get(f"{API_BASE}/stops").json()

# -- Live fetch buses every 20s
@st.cache_data(ttl=20)
def fetch_buses():
    return requests.get(f"{API_BASE}/buses").json()

stops = fetch_stops()
buses = fetch_buses()

# -- Cache last positions for smooth transition
if "last_positions" not in st.session_state:
    st.session_state.last_positions = {}

# -- Base map
m = folium.Map(location=[40.5, -74.45], zoom_start=13, control_scale=True)

# -- Add static stops
for stop in stops:
    try:
        lat = stop["latitude"]
        lon = stop["longitude"]
        name = stop["name"]

        icon_html = f"""
        <div style="
            background-color: white;
            border: 3px solid red;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            box-shadow: 0 0 6px rgba(0,0,0,0.3);
        ">
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            icon=DivIcon(
                icon_size=(18, 18),
                icon_anchor=(9, 9),
                html=icon_html
            ),
            popup=folium.Popup(f"<b>{name}</b>", max_width=200)
        ).add_to(m)
    except Exception as e:
        st.warning(f"Stop error: {e}")

# -- Add live buses (color-coded + smoothed)
for bus in buses:
    lat = bus["lat"]
    lon = bus["lon"]
    color = bus["color"]
    name = bus["name"]
    route = bus["route"]

    # Smooth movement by interpolating toward new position
    last_pos = st.session_state.last_positions.get(bus["id"], (lat, lon))
    interp_lat = last_pos[0] + (lat - last_pos[0]) * 0.5
    interp_lon = last_pos[1] + (lon - last_pos[1]) * 0.5
    st.session_state.last_positions[bus["id"]] = (lat, lon)

    folium.CircleMarker(
        location=[interp_lat, interp_lon],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        popup=f"{name} (Route: {route})"
    ).add_to(m)

# -- Map styling and title spacing
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    iframe {
        height: 85vh !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

st_folium(m, width="100%", height=1100)
