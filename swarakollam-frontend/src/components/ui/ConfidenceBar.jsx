import React from 'react';

export default function ConfidenceBar({ label, value }) {
  const pct = Math.round(Math.max(0, Math.min(1, Number(value) || 0)) * 100);
  return <div className="confidence-row">
    <div className="confidence-copy"><span>{label}</span><strong>{pct}%</strong></div>
    <div className="confidence-track"><div className="confidence-fill" style={{ width: `${pct}%` }} /></div>
  </div>;
}
