import React from 'react';
import { Check, CircleAlert } from 'lucide-react';

export default function StatusPill({ ok, label }) {
  return <span className={`status-pill ${ok ? 'status-ok' : 'status-no'}`}>
    {ok ? <Check size={12} /> : <CircleAlert size={12} />}{label}
  </span>;
}
