import React from 'react';
import { Music2 } from 'lucide-react';

export default function MethodNote({}) {
  return (
    <section className="method-note">
        <div className="method-icon"><Music2 size={18} /></div>
        <div><strong>A computational interpretation, not a classical claim.</strong><p>Pitch, onset, and repetition measurements are feature proxies. They do not identify a raga or guarantee tala recognition. The backend's validation refers to its documented mirror-lattice model.</p></div>
        <span className="method-mark">SW / 01</span>
      </section>
  );
}
