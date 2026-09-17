'use client';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
export default function Page() {
  const router = useRouter();
  useEffect(() => { router.replace('/workspace'); }, [router]);
  return <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)' }}>Redirecting to workspace...</div>;
}
