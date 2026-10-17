import React from 'react';


export default function IntroSection({}) {
  return (
    <section className="intro-row">
        <div>
          <div className="eyebrow"><span>01</span> LISTEN. INTERPRET. TRACE.</div>
          <h1>Sound becomes<br /><em>something you can see.</em></h1>
          <p className="intro-copy">A Carnatic recording, translated into the geometry of a Brahma Mudi kolam. One audio feature at a time, one continuous line.</p>
        </div>
        <div className="intro-stamp" aria-hidden="true">
          <svg viewBox="0 0 130 130" role="presentation"><circle cx="65" cy="65" r="53"/><circle cx="65" cy="65" r="38"/><path d="M65 12V118M12 65H118M27 27L103 103M103 27L27 103"/><circle cx="65" cy="65" r="6" fill="currentColor"/></svg>
          <span>FORM FOLLOWS<br />FREQUENCY</span>
        </div>
      </section>
  );
}
