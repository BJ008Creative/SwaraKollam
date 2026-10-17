import React from 'react';

export default function SiteHeader({apiOnline}) {
  return (
    <header className="topbar">
      <a className="brand" href="#top" aria-label="SwaraKollam home">
        <span className="brand-mark"><span /><span /><span /><span /></span>
        <span className="brand-name">swara<span>kollam</span></span>
      </a>
      <div className="topbar-center"><span className="tiny-dot" /> A STUDY IN SOUND & SYMMETRY</div>
      <div className={`api-status ${apiOnline === true ? 'api-up' : apiOnline === false ? 'api-down' : ''}`}>
        <span className="api-light" />{apiOnline === true ? 'BACKEND CONNECTED' : apiOnline === false ? 'BACKEND OFFLINE' : 'CHECKING API'}
      </div>
    </header>
  );
}
