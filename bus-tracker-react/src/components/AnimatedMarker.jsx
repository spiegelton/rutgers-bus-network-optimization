import { Marker, Popup } from 'react-leaflet';
import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';

function AnimatedMarker({ bus }) {
  const [position, setPosition] = useState([parseFloat(bus.lat), parseFloat(bus.lon)]);
  const markerRef = useRef(null);
  const prevBusId = useRef(bus.id);

  const heading = parseFloat(bus.course) || 0;
  const color = bus.color;

  const busIconBase64 =
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiIgd2lkdGg9IjE2IiBoZWlnaHQ9IjE2IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTMgMWEgMSAxIDAgMCAwIC0xIDF2OS41YTEuNSAxLjUgMCAxIDAgMyAwVjExaDZ2LjVhMS41IDEuNSAwIDEgMCAzIDBWMmExIDEgMCAwIDAgLTEgMUgzem0wIDFoMTB2NkgzVjJ6bTAgN2gxMHYxSDNWOXoiLz48L3N2Zz4=";

  useEffect(() => {
    const target = [parseFloat(bus.lat), parseFloat(bus.lon)];
    const start = position;
    const duration = 1500;

    const startTime = performance.now();

    const animate = (now) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const lat = start[0] + (target[0] - start[0]) * progress;
      const lon = start[1] + (target[1] - start[1]) * progress;
      setPosition([lat, lon]);
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    if (bus.id !== prevBusId.current) {
      // New bus appeared (filter switched, etc) -> snap immediately
      setPosition(target);
      prevBusId.current = bus.id;
    } else {
      // Same bus, just animate position
      requestAnimationFrame(animate);
    }
  }, [bus.lat, bus.lon, bus.id]);

  const icon = L.divIcon({
    className: '',
    html: `
      <div style="position: relative; width: 40px; height: 60px;">
        ${bus.waitSuggestion && bus.waitSuggestion.atStopName ? `
          <div style="
            position: absolute;
            top: -26px;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 2px 6px;
            font-size: 11px;
            border-radius: 6px;
            white-space: nowrap;
            box-shadow: 0 1px 4px rgba(0,0,0,0.3);
          ">
            🕒 Wait ${Math.round(bus.waitSuggestion.waitSeconds / 60)} min at ${bus.waitSuggestion.atStopName}
          </div>
        ` : ''}
  
        <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
          <g transform="rotate(${heading}, 20, 20)">
            <path d="M20,0 A20,20 0 0,1 37.32,10 L20,20 Z" fill="${color}" opacity="0.8"/>
          </g>
          <circle cx="20" cy="20" r="14" fill="${color}" />
          <image href="data:image/svg+xml;base64,${busIconBase64}" x="12" y="12" width="16" height="16" />
        </svg>
      </div>
    `,
    iconSize: [40, 60],
    iconAnchor: [20, 30],
  });  

  return (
    <Marker position={position} icon={icon} ref={markerRef}>
      <Popup>
        <div style={{ fontSize: '14px', fontWeight: 500 }}>
          {bus.route.replace(" Route", "")} Bus #{bus.name}
          <br />
          {bus.paxLoad}% full
          {bus.waitSuggestion && bus.waitSuggestion.atStopName ? (
            <>
              <br />
              <span style={{ color: "red", fontWeight: 600 }}>
                Wait {Math.round(bus.waitSuggestion.waitSeconds / 60)} min at {bus.waitSuggestion.atStopName}
              </span>
            </>
          ) : null}
        </div>
      </Popup>
    </Marker>
  );
}

export default AnimatedMarker;
