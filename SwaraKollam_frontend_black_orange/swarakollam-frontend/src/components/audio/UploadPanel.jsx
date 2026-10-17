import React from 'react';
import { AudioLines, ChevronRight, CircleAlert, FileAudio, LoaderCircle, Sparkles, Upload, X } from 'lucide-react';
import { ACCEPTED_AUDIO_TYPES } from '../../constants.js';

export default function UploadPanel({file, audioUrl, dragging, setDragging, acceptFile, onDrop, fileInput, reset, busy, stage, generate, error}) {
  return (
    <section className="panel upload-panel">
            <div className="panel-heading">
              <div className="section-index">01 / INPUT</div>
              <span className="heading-icon"><AudioLines size={17} /></span>
            </div>
            <h2>Bring a recording.</h2>
            <p className="panel-subtitle">Use a clear 2–45 second excerpt. Instrumental or vocal Carnatic audio works best.</p>
            <div
              className={`dropzone ${dragging ? 'dropzone-active' : ''} ${file ? 'dropzone-loaded' : ''}`}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => !file && fileInput.current?.click()}
              role="button" tabIndex={0}
              onKeyDown={e => { if ((e.key === 'Enter' || e.key === ' ') && !file) fileInput.current?.click(); }}
              aria-label="Choose audio file or drop it here"
            >
              <input ref={fileInput} type="file" accept={ACCEPTED_AUDIO_TYPES} hidden onChange={e => acceptFile(e.target.files?.[0])} />
              {file ? <>
                <div className="file-icon"><FileAudio size={22} /></div>
                <div className="file-info"><strong>{file.name}</strong><span>{(file.size / (1024 * 1024)).toFixed(2)} MB · Ready to analyse</span></div>
                <button className="icon-button remove-file" onClick={e => { e.stopPropagation(); reset(); }} aria-label="Remove audio"><X size={16} /></button>
              </> : <>
                <div className="upload-symbol"><Upload size={21} strokeWidth={1.7} /></div>
                <strong>Drop your audio here</strong>
                <span>or choose a file from your device</span>
                <div className="file-types">WAV <i /> MP3 <i /> OGG <i /> FLAC <i /> M4A</div>
              </>}
            </div>
            {audioUrl && <audio className="audio-player" src={audioUrl} controls preload="metadata" />}
            <div className="upload-footnote"><span>MAX 15 MB</span><span>FIRST 45 SECONDS ANALYSED</span></div>
            <button className="primary-button generate-button" disabled={!file || busy} onClick={generate}>
              {busy ? <><LoaderCircle className="spin" size={17} /> {stage === 'uploading' ? 'UPLOADING AUDIO' : stage === 'rendering' ? 'DRAWING THE LINE' : 'ANALYSING RECORDING'}</> : <><Sparkles size={16} /> GENERATE KOLAM <ChevronRight size={17} /></>}
            </button>
            {busy && <div className="processing-strip"><span className="processing-pulse" />{stage === 'uploading' ? 'Sending the recording to the backend.' : stage === 'rendering' ? 'Rendering the validated line.' : 'Extracting pitch, rhythm and repetition features.'}</div>}
            {error && <div className="error-message" role="alert"><CircleAlert size={16} /><span>{error}</span></div>}
          </section>
  );
}
