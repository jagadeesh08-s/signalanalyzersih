'use client';

import dynamic from 'next/dynamic';
import React from 'react';

// Plotly needs window object, must disable SSR
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => <div style={{ height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)' }}>Loading Visualization...</div>
});

export default Plot;
