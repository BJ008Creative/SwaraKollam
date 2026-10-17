import React, { useEffect, useMemo, useRef, useState } from 'react';
import SiteHeader from './components/layout/SiteHeader.jsx';
import IntroSection from './components/layout/IntroSection.jsx';
import SiteFooter from './components/layout/SiteFooter.jsx';
import MethodNote from './components/layout/MethodNote.jsx';
import UploadPanel from './components/audio/UploadPanel.jsx';
import AudioAnalysisPanel from './components/analysis/AudioAnalysisPanel.jsx';
import PatternPanel from './components/kolam/PatternPanel.jsx';
import ParametersPanel from './components/kolam/ParametersPanel.jsx';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

function prettyError(error, status) {
  if (error) return typeof error === 'string' ? error : 'The audio could not be processed.';
  if (status === 413) return 'This file is larger than the backend upload limit.';
  if (status === 422) return 'The recording may be too short, silent, or missing a usable pitch contour.';
  if (status >= 500) return 'The backend could not complete generation. Check its terminal for details.';
  return 'Could not connect to the backend. Check that FastAPI is running and the API URL is correct.';
}

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener?.('change', update);
    return () => query.removeEventListener?.('change', update);
  }, []);
  return reduced;
}

export default function App() {
  const [file, setFile] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [replayKey, setReplayKey] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [apiOnline, setApiOnline] = useState(null);
  const [showAllNotes, setShowAllNotes] = useState(false);
  const fileInput = useRef(null);
  const patternRef = useRef(null);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    fetch(`${API_BASE}/health`).then(r => setApiOnline(r.ok)).catch(() => setApiOnline(false));
  }, []);

  useEffect(() => {
    return () => { if (audioUrl) URL.revokeObjectURL(audioUrl); };
  }, [audioUrl]);

  useEffect(() => {
    if (!result?.kolam?.svg) return;
    const root = patternRef.current;
    if (!root) return;
    const path = root.querySelector('.kolam-curve');
    if (!path) return;
    if (reducedMotion) {
      path.style.strokeDasharray = 'none';
      path.style.strokeDashoffset = '0';
      setPlaying(false);
      return;
    }
    path.style.strokeDasharray = '1';
    path.style.strokeDashoffset = '1';
    path.style.animation = 'none';
    void path.getBoundingClientRect();
    path.style.animation = 'draw-line 3.8s cubic-bezier(.3,.02,.22,1) forwards';
    setPlaying(true);
    const timer = window.setTimeout(() => setPlaying(false), 3900);
    return () => window.clearTimeout(timer);
  }, [result, replayKey, reducedMotion]);

  const features = result?.features;
  const params = result?.params;
  const kolam = result?.kolam;
  const validationItems = useMemo(() => {
    if (!kolam?.validation) return [];
    return Object.entries(kolam.validation).map(([key, value]) => ({
      key,
      label: key.replaceAll('_', ' '),
      value: Boolean(value),
    }));
  }, [kolam]);

  function acceptFile(next) {
    if (!next) return;
    const extension = next.name.split('.').pop()?.toLowerCase();
    if (!['wav', 'mp3', 'ogg', 'flac', 'm4a'].includes(extension)) {
      setError('Choose a WAV, MP3, OGG, FLAC, or M4A audio file.');
      return;
    }
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setFile(next);
    setAudioUrl(URL.createObjectURL(next));
    setError('');
    setResult(null);
    setStage('ready');
    setPlaying(false);
  }

  function onDrop(event) {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files?.[0]);
  }

  async function generate() {
    if (!file || busy) return;
    setBusy(true);
    setError('');
    setStage('uploading');
    setResult(null);
    const form = new FormData();
    form.append('audio', file);
    try {
      setStage('analysing');
      const response = await fetch(`${API_BASE}/generate`, { method: 'POST', body: form });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = payload?.detail;
        throw Object.assign(new Error(prettyError(detail, response.status)), { status: response.status });
      }
      if (!payload?.features || !payload?.params || !payload?.kolam?.svg) {
        throw new Error('The backend response is missing features, parameters, or the generated SVG.');
      }
      setStage('rendering');
      setResult(payload);
      setReplayKey(k => k + 1);
      setStage('done');
      setApiOnline(true);
    } catch (err) {
      setError(prettyError(err.message, err.status));
      setStage('error');
      if (!err.status) setApiOnline(false);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(''); setFile(null); setResult(null); setError(''); setStage('idle'); setPlaying(false);
    if (fileInput.current) fileInput.current.value = '';
  }

  function replay() {
    if (!kolam?.svg) return;
    setReplayKey(k => k + 1);
  }

  function downloadPng() {
    if (!kolam?.svg) return;
    const svgBlob = new Blob([kolam.svg], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = 1800; canvas.height = 1800;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#fffdf8'; ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob(blob => {
        if (!blob) { setError('PNG export failed in this browser.'); return; }
        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `swarakollam-${params?.grid_size || 'pattern'}-grid.png`;
        link.click();
        URL.revokeObjectURL(downloadUrl);
      }, 'image/png');
    };
    image.onerror = () => { URL.revokeObjectURL(url); setError('The generated SVG could not be converted to PNG.'); };
    image.src = url;
  }

  function downloadSvg() {
    if (!kolam?.svg) return;
    const url = URL.createObjectURL(new Blob([kolam.svg], { type: 'image/svg+xml;charset=utf-8' }));
    const a = document.createElement('a'); a.href = url;
    a.download = `swarakollam-${params?.grid_size || 'pattern'}-grid.svg`; a.click();
    URL.revokeObjectURL(url);
  }

  const notes = features?.notes || [];
  const shownNotes = showAllNotes ? notes : notes.slice(0, 3);

  return <div className="app-shell">
    <SiteHeader apiOnline={apiOnline} />

    <main id="top">
      <IntroSection />

      <section className="workbench" aria-label="Audio to kolam workbench">
        <div className="left-column">
          <UploadPanel file={file} audioUrl={audioUrl} dragging={dragging} setDragging={setDragging} acceptFile={acceptFile} onDrop={onDrop} fileInput={fileInput} reset={reset} busy={busy} stage={stage} generate={generate} error={error} />

          <AudioAnalysisPanel features={features} params={params} showAllNotes={showAllNotes} setShowAllNotes={setShowAllNotes} notes={notes} shownNotes={shownNotes} />
        </div>

        <div className="right-column">
          <PatternPanel kolam={kolam} params={params} patternRef={patternRef} replay={replay} playing={playing} downloadPng={downloadPng} downloadSvg={downloadSvg} validationItems={validationItems} replayKey={replayKey} />
          <ParametersPanel params={params} />
        </div>
      </section>

      <MethodNote />
    </main>

    <SiteFooter />
  </div>;
}
