import React from 'react';

export default function ParametersPanel({params}) {
  return (
    <section className="panel params-panel">
            <div className="panel-heading"><div className="section-index">04 / PATTERN PARAMETERS</div><span className="heading-icon"><Grid2X2 size={16} /></span></div>
            <h2>Geometry, in numbers.</h2>
            <p className="panel-subtitle">The mapped values passed to the procedural generator.</p>
            <div className="param-grid">
              <div className="param-card"><span>GRID SIZE</span><strong>{params ? `${params.grid_size} × ${params.grid_size}` : '—'}</strong><small>Pulli arrangement</small></div>
              <div className="param-card"><span>SYMMETRY</span><strong>{params ? params.symmetry.replace('_', ' ') : '—'}</strong><small>Pattern constraint</small></div>
              <div className="param-card"><span>TURN DENSITY</span><strong>{params ? `${Math.round(params.turn_density * 100)}%` : '—'}</strong><small>Local direction changes</small></div>
              <div className="param-card"><span>CROSSING DENSITY</span><strong>{params ? `${Math.round((params.crossing_density ?? 0) * 100)}%` : '—'}</strong><small>Strand crossing tendency</small></div>
            </div>
            <div className="seed-line"><span>DETERMINISTIC SEED</span><code>{params ? params.seed : 'Generated from audio features'}</code><button className="text-button" disabled={!params} onClick={() => navigator.clipboard?.writeText(String(params.seed))}>COPY</button></div>
          </section>
  );
}
