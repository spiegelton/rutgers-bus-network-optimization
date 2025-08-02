import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import AnimatedMarker from './AnimatedMarker';
import { useEffect, useState } from 'react';
import axios from 'axios';

function MapView({ buses, stops }) {
  const [etas, setEtas] = useState({});
  const [polylines, setPolylines] = useState({});
  const [selectedRoute, setSelectedRoute] = useState(null);

  const routeColors = {
    EE: "#FF8000", F: "#FF0000", REXL: "#66B2FF", REXB: "#663300",
    A: "#FF00FF", H: "#000099", C: "#008080", LX: "#cc99ff",
    B: "#FFFF00", "B/L Loop": "#996633"
  };

  const fetchEta = async (stopId) => {
    try {
      const res = await axios.get(`http://localhost:8000/eta/${stopId}`);
      setEtas((prev) => ({
        ...prev,
        [stopId]: res.data,
      }));
    } catch (err) {
      console.error('Error fetching ETA:', err);
    }
  };

  useEffect(() => {
    const routes = Object.keys(routeColors);
    Promise.all(
      routes.map(route =>
        fetch(`http://localhost:8000/route_polyline/${route.replace("/", "_")}`)
          .then(res => res.ok ? res.json() : null)
          .then(data => ({ route, coords: data }))
          .catch(() => null)
      )
    ).then(results => {
      const polyDict = {};
      results.forEach(item => {
        if (item && item.coords) {
          polyDict[item.route] = item.coords;
        }
      });
      setPolylines(polyDict);
    });
  }, []);

  const stopIcon = L.divIcon({
    className: 'stop-icon',
    html: `
      <div style="
        width: 14px;
        height: 14px;
        background-color: white;
        border: 3px solid red;
        border-radius: 50%;
        box-shadow: 0 0 4px rgba(0,0,0,0.2);
      ">
      </div>
    `,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });

  // Filtered data based on route
  const filteredBuses = selectedRoute
    ? buses.filter(bus => bus.route.replace(" Route", "") === selectedRoute)
    : buses;

  const filteredStops = selectedRoute
    ? stops.filter(stop => stop.routes?.some(r => r.replace(" Route", "") === selectedRoute))
    : stops;

  return (
    <>
      {/* ROUTE TOGGLES */}
      <div style={{
        position: 'absolute',
        zIndex: 1000,
        top: 10,
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'white',
        padding: 8,
        borderRadius: 6,
        display: 'flex',
        gap: '6px'
      }}>

        {Object.keys(routeColors).map(route => {
          const shortName = route.replace(" Route", "");
          const isSelected = selectedRoute === shortName;
          return (
            <button
              key={route}
              onClick={() => setSelectedRoute(isSelected ? null : shortName)}
              style={{
                backgroundColor: isSelected ? routeColors[shortName] : '#f0f0f0',
                color: isSelected ? 'white' : 'black',
                border: `2px solid ${routeColors[shortName]}`,
                borderRadius: '8px',
                padding: '4px 10px',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              {shortName}
            </button>
          );
        })}
      </div>

      <MapContainer center={[40.5, -74.45]} zoom={13} style={{ height: '100vh', width: '100%' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
        />

        {/* ROUTE POLYLINES */}
        {Object.entries(polylines).map(([route, coords]) => {
          const shortName = route.replace(" Route", "");
          const color = selectedRoute
            ? (shortName === selectedRoute ? routeColors[shortName] || "blue" : null)
            : "red";

          if (!color) return null;

          return (
            <Polyline
              key={`poly-${route}`}
              positions={coords.map(([lat, lon]) => [lat, lon])}
              pathOptions={{ color, weight: 4, opacity: 0.7 }}
            />
          );
        })}

        {/* STOPS */}
        {filteredStops.map((stop, idx) => {
          const lat = parseFloat(stop.latitude);
          const lon = parseFloat(stop.longitude);
          if (isNaN(lat) || isNaN(lon)) return null;

          return (
            <Marker
              key={`stop-${idx}`}
              position={[lat, lon]}
              icon={stopIcon}
              eventHandlers={{ click: () => fetchEta(stop.id) }}
            >
              <Popup>
                <div>
                  <strong>{stop.name}</strong>
                  <div style={{ marginTop: '8px' }}>
                    {etas[stop.id] ? (
                      etas[stop.id].length > 0 ? (
                        (() => {
                          const grouped = etas[stop.id].reduce((acc, bus) => {
                            const route = bus.route;
                            const etaText = bus.eta.toLowerCase().replace("min", "").trim();
                            const eta = etaText.includes("arriv") || etaText.includes("due") || etaText.includes("less")
                              ? 0
                              : parseInt(etaText) || 999;
                            const routeShort = route.replace(" Route", "");
                            if (!acc[routeShort]) acc[routeShort] = [];
                            acc[routeShort].push({ eta: eta, label: bus.eta });
                            return acc;
                          }, {});

                          return Object.entries(grouped)
                            .sort((a, b) => a[1][0].eta - b[1][0].eta)
                            .map(([routeShort, etaList], i) => {
                              const badgeColor = routeColors[routeShort] || "#999";
                              const etaLabels = etaList
                                .sort((a, b) => a.eta - b.eta)
                                .slice(0, 3)
                                .map(e => e.label)
                                .join(", ");
                              return (
                                <div key={i} style={{ marginBottom: "4px" }}>
                                  <span style={{
                                    backgroundColor: badgeColor,
                                    color: "#fff",
                                    padding: "2px 6px",
                                    borderRadius: "8px",
                                    fontSize: "12px",
                                    fontWeight: "bold",
                                    marginRight: "6px"
                                  }}>{routeShort}</span>
                                  {etaLabels}
                                </div>
                              );
                            });
                        })()
                      ) : (
                        <div>No buses arriving soon</div>
                      )
                    ) : (
                      <div>Loading ETA...</div>
                    )}
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* BUSES */}
        {filteredBuses.map((bus, idx) => {
          const lat = parseFloat(bus.lat);
          const lon = parseFloat(bus.lon);
          if (isNaN(lat) || isNaN(lon)) return null;

          return (
            <AnimatedMarker key={bus.id} bus={bus} />
          );
        })}
      </MapContainer>
    </>
  );
}

export default MapView;
