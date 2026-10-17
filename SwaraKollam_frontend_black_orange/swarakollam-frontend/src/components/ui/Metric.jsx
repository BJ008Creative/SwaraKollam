import React from 'react';

export default function Metric({ label, value, unit, detail, accent = false }) {
  return <div className={`metric ${accent ? 'metric-accent' : ''}`}>
    <div className="metric-label">{label}</div>
    <div className="metric-value">{value ?? '—'}<span>{unit || ''}</span></div>
    {detail && <div className="metric-detail">{detail}</div>}
  </div>;
}
