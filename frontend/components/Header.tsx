'use client';

import { useState } from 'react';

interface HeaderProps {
  currentJob?: { id: number; filename: string; status: string; progress: number } | null;
  presentationMode?: boolean;
  onTogglePresentation?: () => void;
}

export default function Header({ currentJob, presentationMode, onTogglePresentation }: HeaderProps) {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.classList.toggle('light', next === 'light');
    document.documentElement.classList.toggle('dark', next === 'dark');
  };

  return (
    <header className="header" style={{
      position: 'fixed',
      top: 0,
      left: 'var(--sidebar-width)',
      right: 0,
      height: 'var(--header-height)',
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-primary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      zIndex: 40,
      backdropFilter: 'blur(8px)',
    }}>
      {/* Left: App name + current session */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
          Automated RF Signal Analysis
        </span>
        {currentJob && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '4px 12px',
            borderRadius: 6,
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-primary)',
            fontSize: 12,
          }}>
            <span style={{ color: 'var(--text-secondary)' }}>{currentJob.filename}</span>
            <span style={{
              width: 6, height: 6, borderRadius: '50%',
              background: currentJob.status === 'completed' ? 'var(--status-success)'
                : currentJob.status === 'processing' ? 'var(--signal-cyan)'
                : currentJob.status === 'failed' ? 'var(--status-error)'
                : 'var(--status-pending)',
            }} />
            {currentJob.status === 'processing' && (
              <span className="mono" style={{ color: 'var(--signal-cyan)', fontSize: 11 }}>
                {Math.round(currentJob.progress)}%
              </span>
            )}
          </div>
        )}
      </div>

      {/* Right: Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {onTogglePresentation && (
          <button
            onClick={onTogglePresentation}
            style={{
              padding: '6px 12px',
              borderRadius: 6,
              border: presentationMode ? '1px solid var(--signal-cyan)' : '1px solid var(--border-secondary)',
              background: presentationMode ? 'rgba(0,212,255,0.1)' : 'transparent',
              color: presentationMode ? 'var(--signal-cyan)' : 'var(--text-secondary)',
              fontSize: 12,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {presentationMode ? '✦ Presentation ON' : '▣ Presentation'}
          </button>
        )}
        <button
          onClick={toggleTheme}
          style={{
            padding: '6px 12px',
            borderRadius: 6,
            border: '1px solid var(--border-secondary)',
            background: 'transparent',
            color: 'var(--text-secondary)',
            fontSize: 12,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          {theme === 'dark' ? '☀ Light' : '◑ Dark'}
        </button>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: '50%',
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 13,
          color: 'var(--text-secondary)',
          cursor: 'pointer',
        }}>
          U
        </div>
      </div>
    </header>
  );
}
