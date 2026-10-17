import React from 'react';
import { Check, Download, Pause, Play, X } from 'lucide-react';

export default function PatternPanel({kolam, params, patternRef, replay, playing, downloadPng, downloadSvg, validationItems, replayKey}) {
  return (
    <section className="panel canvas-panel">
            <div className="canvas-topline">
              <div><div className="section-index">03 / GENERATED FORM</div><h2>The line, made visible.</h2></div>
              <span className={`validation-badge ${kolam?.validated ? 'validation-pass' : kolam ? 'validation-fail' : 'validation-wait'}`}><span />{kolam ? (kolam.validated ? 'VALIDATED' : 'NOT VALIDATED') : 'NO OUTPUT YET'}</span>
            </div>
            <div className="artboard" ref={patternRef} key={kolam ? `pattern-${replayKey}` : 'empty'}>
              {kolam?.svg ? <div className="pattern-svg" dangerouslySetInnerHTML={{ __html: kolam.svg }} /> : <div className="artboard-empty">
                <svg className="placeholder-kolam" viewBox="0 0 360 360" aria-hidden="true">
                  <g fill="none" stroke="currentColor" strokeWidth="1.1" opacity=".34">
                    <path d="M180 34 C225 34 225 79 180 79 C135 79 135 124 180 124 C225 124 225 169 180 169 C135 169 135 214 180 214 C225 214 225 259 180 259 C135 259 135 304 180 304" />
                    <path d="M34 180 C34 135 79 135 79 180 C79 225 124 225 124 180 C124 135 169 135 169 180 C169 225 214 225 214 180 C214 135 259 135 259 180 C259 225 304 225 304 180" />
                    <path d="M75 75 C120 75 120 120 75 120 C75 165 120 165 120 120 C165 120 165 165 120 165 C120 210 165 210 165 165 C210 165 210 210 165 210 C165 255 210 255 210 210 C255 210 255 255 210 255 C210 300 255 300 255 255" />
                    <circle cx="180" cy="180" r="130" strokeDasharray="3 7" />
                  </g>
                  <g fill="currentColor" opacity=".6">{Array.from({length: 7}, (_, i) => Array.from({length: 7}, (_, j) => <circle key={`${i}-${j}`} cx={70 + i * 36.5} cy={70 + j * 36.5} r="2" />))}</g>
                </svg>
                <span className="empty-overline">YOUR CANVAS IS READY</span>
                <strong>Waiting for a sound.</strong>
                <p>Your generated line will appear here, drawn over the pulli grid.</p>
              </div>}
              {kolam && <div className="canvas-corner-label">{params.grid_size} × {params.grid_size} PULLI GRID</div>}
            </div>
            <div className="canvas-actions">
              <button className="secondary-button" disabled={!kolam} onClick={replay}>{playing ? <><Pause size={15} /> REPLAY LINE</> : <><Play size={15} /> REPLAY LINE</>}</button>
              <div className="download-actions">
                <button className="primary-button download-button" disabled={!kolam} onClick={downloadPng}><Download size={15} /> DOWNLOAD PNG</button>
                <button className="icon-button svg-download" disabled={!kolam} onClick={downloadSvg} title="Download SVG" aria-label="Download SVG"><Download size={16} /><span>SVG</span></button>
              </div>
            </div>
            {kolam && <div className="pattern-meta">
              <div><span>REQUESTED SYMMETRY</span><strong>{kolam.symmetry_requested?.replace('_', ' ') || params.symmetry}</strong></div>
              <div><span>APPLIED SYMMETRY</span><strong>{kolam.symmetry_applied?.replace('_', ' ') || params.symmetry}</strong></div>
              <div><span>REPAIR STEPS</span><strong>{kolam.repairs ?? '—'}</strong></div>
              <div><span>ATTEMPTS</span><strong>{kolam.attempts ?? '—'}</strong></div>
            </div>}
            {kolam && <div className="validation-section">
              <div className="subhead"><span>STRUCTURAL CHECKS</span><span className="subhead-note">GENERATOR VALIDATION</span></div>
              <div className="validation-list">{validationItems.map(item => <div className="validation-item" key={item.key}><span className={`validation-check ${item.value ? 'is-true' : 'is-false'}`}>{item.value ? <Check size={12} /> : <X size={12} />}</span><span>{item.label}</span><span className="validation-result">{item.value ? 'PASS' : 'FAIL'}</span></div>)}</div>
              {kolam.message && <p className="generator-message">{kolam.message}</p>}
            </div>}
          </section>
  );
}
