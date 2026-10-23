import { useState } from 'react';
import { isValidLat, isValidLon } from '../shared/utils/validation';

interface Props { onSubmit: (lat: number, lon: number) => void; loading: boolean; }

export function LocationInput({ onSubmit, loading }: Props) {
  const [lat, setLat] = useState('');
  const [lon, setLon] = useState('');

  const submit = () => {
    const la = parseFloat(lat);
    const lo = parseFloat(lon);
    if (!isValidLat(la) || !isValidLon(lo)) { alert('Valid range: Lat -90 to 90, Lon -180 to 180'); return; }
    onSubmit(la, lo);
  };

  const useDemo = () => { setLat('13.750'); setLon('100.500'); onSubmit(13.75, 100.5); };

  return (
    <div className="card">
      <h2 style={{ marginBottom: 12 }}>Check Air Quality</h2>
      <label style={{ fontSize: '0.85rem', color: '#666', display: 'block', marginBottom: 4 }} htmlFor="lat">Latitude</label>
      <input id="lat" className="input-field" type="number" step="0.001" min="-90" max="90" placeholder="13.750" value={lat} onChange={e => setLat(e.target.value)} style={{ marginBottom: 12 }} />
      <label style={{ fontSize: '0.85rem', color: '#666', display: 'block', marginBottom: 4 }} htmlFor="lon">Longitude</label>
      <input id="lon" className="input-field" type="number" step="0.001" min="-180" max="180" placeholder="100.500" value={lon} onChange={e => setLon(e.target.value)} style={{ marginBottom: 16 }} />
      <div style={{ display: 'flex', gap: 10 }}>
        <button className="btn btn-primary" style={{ flex: 1 }} onClick={submit} disabled={loading}>{loading ? 'Loading...' : 'Check PM2.5'}</button>
        <button className="btn btn-secondary" style={{ flex: 1 }} onClick={useDemo} disabled={loading}>Demo (Bangkok)</button>
      </div>
    </div>
  );
}
