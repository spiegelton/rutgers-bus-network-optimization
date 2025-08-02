import { useEffect, useState } from 'react'
import MapView from './components/MapView'
import axios from 'axios'

function App() {
  const [buses, setBuses] = useState([])
  const [stops, setStops] = useState([])

  const fetchData = async () => {
    const busRes = await axios.get('http://localhost:8000/buses');
    setBuses(busRes.data);
  };
  
  const fetchStops = async () => {
    const stopRes = await axios.get('http://localhost:8000/stops');
    setStops(stopRes.data);
  };
  
  useEffect(() => {
    fetchStops();   // only once when page loads
    fetchData();    // initial bus fetch
    const interval = setInterval(fetchData, 10000); // only bus refresh every 10s
    return () => clearInterval(interval);
  }, []);  

  return <MapView buses={buses} stops={stops} />
}

export default App
