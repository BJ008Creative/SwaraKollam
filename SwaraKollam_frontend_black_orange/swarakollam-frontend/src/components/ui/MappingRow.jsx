import React from 'react';
import { ChevronRight } from 'lucide-react';

export default function MappingRow({ source, value, target, note }) {
  return <div className="mapping-row">
    <div className="mapping-source"><span>{source}</span><strong>{value}</strong></div>
    <ChevronRight className="mapping-arrow" size={15} strokeWidth={1.6} />
    <div className="mapping-target"><strong>{target}</strong><span>{note}</span></div>
  </div>;
}
