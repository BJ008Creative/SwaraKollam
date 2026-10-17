import React from 'react';
import { Waves, ChevronRight } from 'lucide-react';
import Metric from '../ui/Metric.jsx';
import ConfidenceBar from '../ui/ConfidenceBar.jsx';
import MappingRow from '../ui/MappingRow.jsx';

export default function AudioAnalysisPanel({features, params, showAllNotes, setShowAllNotes, notes, shownNotes}) {
  return (
    <section className="panel features-panel">
            <div className="panel-heading">
              <div className="section-index">02 / AUDIO READOUT</div>
              <span className="live-tag">{features ? 'ANALYSED' : 'AWAITING AUDIO'}</span>
            </div>
            <h2>What the sound tells us.</h2>
            <p className="panel-subtitle">Features extracted from the recording. Values appear here after processing.</p>
            <div className="metric-grid">
              <Metric label="TEMPO ESTIMATE" value={features ? Math.round(features.tempo_bpm) : '—'} unit={features ? ' BPM' : ''} detail="Onset rhythm" accent />
              <Metric label="PITCH RANGE" value={features ? Math.round(features.pitch_range_cents).toLocaleString() : '—'} unit={features ? ' ¢' : ''} detail="Cents, tonic-relative" />
              <Metric label="PITCH CLASSES" value={features ? features.distinct_pitch_count : '—'} detail="Distinct bins" />
              <Metric label="GAMAKA PROXY" value={features ? `${Math.round(features.gamaka_intensity * 100)}%` : '—'} detail="Pitch motion, not classification" />
              <Metric label="REPETITION" value={features ? `${Math.round(features.symmetry_score * 100)}%` : '—'} detail="Contour similarity" />
              <Metric label="CYCLE LENGTH" value={features ? (features.cycle_beats ? `${features.cycle_beats}` : '—') : '—'} unit={features?.cycle_beats ? ' beats' : ''} detail={features ? (features.cycle_beats ? 'Estimated cycle' : 'No reliable estimate') : 'Tala-like proxy'} />
            </div>
            <div className="confidence-block">
              <div className="subhead"><span>ESTIMATION CONFIDENCE</span><span className="subhead-note">0–100%</span></div>
              <ConfidenceBar label="Tempo" value={features?.confidence?.tempo} />
              <ConfidenceBar label="Pitch" value={features?.confidence?.pitch} />
              <ConfidenceBar label="Cycle" value={features?.confidence?.cycle} />
            </div>
            <div className="mapping-block">
              <div className="subhead"><span>HOW FEATURES BECOME FORM</span><span className="subhead-note">MAPPING LOGIC</span></div>
              {features && params ? <div className="mapping-list">
                <MappingRow source="Pitch range + pitch classes" value={`${Math.round(features.pitch_range_cents)}¢ · ${features.distinct_pitch_count} bins`} target={`${params.grid_size} × ${params.grid_size} grid`} note="Musical variation informs grid complexity" />
                <MappingRow source="Contour repetition" value={`${Math.round(features.symmetry_score * 100)}%`} target={params.symmetry.replace('_', ' ')} note="Repeated or mirrored phrases influence symmetry" />
                <MappingRow source="Gamaka + tempo" value={`${Math.round(features.gamaka_intensity * 100)}% · ${Math.round(features.tempo_bpm)} BPM`} target={`${Math.round(params.turn_density * 100)}% turn density`} note="Pitch motion and pulse shape the turning rate" />
                <MappingRow source="Feature signature" value={features.contour_signature ? `${features.contour_signature.slice(0, 12)}…` : `Seed ${params.seed}`} target={`Seed ${params.seed}`} note="Stable seed makes the same analysis reproducible" />
                <MappingRow source="Tempo + cycle proxy" value={`${Math.round(features.tempo_bpm)} BPM · ${features.cycle_beats ?? 'unknown'} beats`} target={`${Math.round((params.crossing_density ?? 0) * 100)}% crossing density`} note="Rhythmic estimates influence crossing distribution" />
              </div> : <div className="empty-mapping"><div className="empty-mapping-icon"><Waves size={18} /></div><div><strong>Mapping appears after analysis</strong><span>Upload audio to see each measured feature alongside the Kolam parameter it influences.</span></div></div>}
            </div>
            {features && notes.length > 0 && <div className="analysis-notes">
              <button className="text-button notes-toggle" onClick={() => setShowAllNotes(v => !v)}>{showAllNotes ? 'Hide analysis notes' : `Read analysis notes (${notes.length})`} <ChevronRight size={14} /></button>
              {shownNotes.map((note, i) => <p key={i} className="note-line">{note}</p>)}
            </div>}
          </section>
  );
}
