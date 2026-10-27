'use client';
export default function ErrorPage({reset}:{reset:()=>void}) {return <main className="standalone"><div className="empty-card"><h1>We couldn’t load this page</h1><p>The service may be temporarily unavailable. Please try again.</p><button className="primary" onClick={reset}>Try again</button></div></main>;}
