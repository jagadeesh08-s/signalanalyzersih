'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/', icon: '◈' },
  { label: 'Upload & Analyze', href: '/upload', icon: '↑' },
  { label: 'Analysis History', href: '/history', icon: '☰' },
  { type: 'divider' as const, label: '', href: '' },
  { label: 'Workspace', href: '/workspace', icon: '⬡' },
  { type: 'divider' as const, label: '', href: '' },
  { label: 'Settings', href: '/settings', icon: '⚙' },
  { label: 'Documentation', href: '/docs', icon: '?' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar" style={{
      position: 'fixed',
      left: 0,
      top: 0,
      width: 'var(--sidebar-width)',
      height: '100vh',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border-primary)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 50,
      overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-primary)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
      }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: 'var(--gradient-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 16,
          fontWeight: 800,
          color: '#0a0e17',
        }}>
          S
        </div>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
            SIH26147
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', letterSpacing: '0.5px' }}>
            SIGNAL ANALYZER
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 10px' }}>
        {NAV_ITEMS.map((item, idx) => {
          if ('type' in item && item.type === 'divider') {
            return <div key={idx} style={{
              height: 1,
              background: 'var(--border-primary)',
              margin: '8px 10px',
            }} />;
          }
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 12px',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'var(--signal-cyan)' : 'var(--text-secondary)',
                background: isActive ? 'rgba(0, 212, 255, 0.08)' : 'transparent',
                textDecoration: 'none',
                transition: 'all 0.15s ease',
                marginBottom: 2,
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.background = 'var(--bg-tertiary)';
                  e.currentTarget.style.color = 'var(--text-primary)';
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
            >
              <span style={{ fontSize: 16, width: 20, textAlign: 'center' }}>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '12px 20px',
        borderTop: '1px solid var(--border-primary)',
        fontSize: 10,
        color: 'var(--text-muted)',
      }}>
        SIH26147 v1.0 • Signal Intelligence
      </div>
    </aside>
  );
}
