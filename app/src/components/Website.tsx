import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Heart, ArrowRight, ShieldCheck, CalendarDays, Stethoscope, Users, Smartphone, Menu, X, Search } from 'lucide-react';
import { care } from '../data/care';
import { openAccount } from './Sections';
import type { IconText, CareService } from '../data/care';

function AmbientScene() {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let disposed = false;
    let cleanup: (() => void) | undefined;
    void import('three').then(THREE => {
      if (disposed || !host.current) return;
      const container = host.current;
      let renderer: import('three').WebGLRenderer;
      try { renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' }); } catch { return; }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 20);
      camera.position.z = 7;
      const geometry = new THREE.TorusGeometry(1.7, 0.006, 6, 120);
      const material = new THREE.MeshBasicMaterial({ color: '#9aaeff', transparent: true, opacity: 0.28 });
      const rings = new THREE.Group();
      for (let i = 0; i < 3; i++) {
        const ring = new THREE.Mesh(geometry, material);
        ring.rotation.set(0.2 + i * 0.35, 0.3 + i * 0.3, i * 0.6); rings.add(ring);
      }
      scene.add(rings); container.appendChild(renderer.domElement);
      const resize = () => {
        const { width, height } = container.getBoundingClientRect();
        renderer.setSize(width, height); camera.aspect = width / Math.max(height, 1); camera.updateProjectionMatrix();
      };
      const observer = new ResizeObserver(resize); observer.observe(container);
      const render = () => { rings.rotation.z += 0.0006; renderer.render(scene, camera); };
      const visibility = new IntersectionObserver(([entry]) => renderer.setAnimationLoop(entry.isIntersecting && !document.hidden ? render : null));
      visibility.observe(container);
      const onVisibility = () => renderer.setAnimationLoop(!document.hidden && container.getBoundingClientRect().bottom > 0 ? render : null);
      document.addEventListener('visibilitychange', onVisibility); resize();
      cleanup = () => {
        renderer.setAnimationLoop(null); observer.disconnect(); visibility.disconnect();
        document.removeEventListener('visibilitychange', onVisibility);
        geometry.dispose(); material.dispose(); renderer.dispose(); renderer.domElement.remove();
      };
    }).catch(() => { /* Static decoration remains if WebGL is unavailable. */ });
    return () => { disposed = true; cleanup?.(); };
  }, []);
  return <div className="ambient-scene" ref={host} aria-hidden="true" />;
}

export function Logo({tagline}: {tagline?:string} = {}) {
  return <Link className="brand" to="/" aria-label="FamilyCare+ home"><span className="logo"><Heart fill="currentColor" /><Users className="logo-people" /></span><span><strong>FamilyCare<span>+</span></strong><small>{tagline ?? 'Healthier Families. Brighter Tomorrows.'}</small></span></Link>;
}

export function Header() {
  const [open, setOpen] = useState(false);
  const [dialog, setDialog] = useState<'Login' | 'Sign Up' | 'Doctors' | 'Contact' | 'Search' | null>(null);
  const [query, setQuery] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const showAccount = (event: Event) => navigate((event as CustomEvent).detail === 'Doctor' ? '/doctor/signup' : '/customer/signup');
    window.addEventListener('familycare-account', showAccount);
    return () => window.removeEventListener('familycare-account', showAccount);
  }, [navigate]);
  useEffect(() => { setOpen(false); setDialog(null); }, [location.pathname, location.hash]);
  useEffect(() => {
    if (!dialog) return;
    const trigger = document.activeElement as HTMLElement;
    closeRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setDialog(null);
      if (event.key === 'Tab') {
        const elements = Array.from(document.querySelectorAll<HTMLElement>('.role-dialog button, .role-dialog a, .role-dialog input'));
        const first = elements[0]; const last = elements[elements.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    window.addEventListener('keydown', keyboard);
    return () => { document.body.style.overflow = previousOverflow; window.removeEventListener('keydown', keyboard); trigger?.focus(); };
  }, [dialog]);
  const results = care.filter(item => `${item.title} ${item.detail} ${item.items.map(([, text]) => text).join(' ')} ${item.id === 'adult' ? 'BP' : ''}`.toLowerCase().includes(query.trim().toLowerCase()));
  return <>
    <header><Logo /><button className="mobile-toggle" aria-label="Toggle navigation" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
      <nav className={open ? 'open' : ''} aria-label="Main navigation"><NavLink to="/" end>Home</NavLink><NavLink to="/about">About Us</NavLink><NavLink to="/services">Services</NavLink><NavLink to="/for-doctors">For Doctors</NavLink><NavLink to="/contact">Contact</NavLink></nav>
      <div className="auth"><button className="search-button" aria-label="Search services" onClick={() => setDialog('Search')}><Search size={21} /></button><Link className="button outline" to="/customer/login">Login</Link><Link className="button primary" to="/customer/signup">Sign Up <ArrowRight size={17} /></Link></div>
    </header>
    {dialog && <div className="modal-backdrop" onClick={() => setDialog(null)}><section className="role-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onClick={e => e.stopPropagation()}>
      <button ref={closeRef} className="close" onClick={() => setDialog(null)} aria-label="Close dialog"><X /></button><span className="eyebrow">FAMILYCARE+</span>
      <h2 id="dialog-title">{dialog === 'Search' ? 'Find your care' : dialog === 'Doctors' ? 'Care starts with you.' : dialog === 'Contact' ? 'Let’s connect.' : `${dialog} with FamilyCare+`}</h2>
      {dialog === 'Search' ? <><label className="search-label" htmlFor="care-search">Search our services</label><input id="care-search" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Try vaccination, pregnancy or BP" /><div className="search-results">{results.map(item => <Link key={item.id} to={`/services#${item.id}`} onClick={() => setDialog(null)}>{item.title}<ArrowRight size={18} /></Link>)}{!results.length && <p>No matching services. Try child care, pregnancy or blood pressure.</p>}</div></> : <><p>{dialog === 'Doctors' ? 'The dedicated doctor portal is being prepared. Explore our care areas to learn about the families we aim to support.' : dialog === 'Contact' ? 'Contact details will be added when FamilyCare+ launches. You can explore our services in the meantime.' : 'Customer and doctor accounts will have separate registration and login. Account access is coming in the next phase.'}</p><Link to="/services#care-options" className="button primary" onClick={() => setDialog(null)}>Explore our services <ArrowRight size={17} /></Link></>}
    </section></div>}
  </>;
}

function Benefits() {
  const items: IconText[] = [[Stethoscope, 'Expert', 'Care'], [ShieldCheck, 'Secure &', 'Private'], [CalendarDays, 'Care for', 'Every Stage'], [Heart, 'Personalized', 'Care']];
  return <div className="benefits">{items.map(([Icon, a, b], i) => <div key={a}><span className={`icon-circle tone-${i}`}><Icon /></span><span>{a}<br />{b}</span></div>)}</div>;
}
export function Hero({ about = false }: { about?: boolean }) {
  return <section className="hero"><AmbientScene /><div className="hero-copy"><span className="eyebrow">{about ? 'ONE FAMILY. EVERY STAGE. ALWAYS.' : 'CARE FOR TODAY, TOMORROW AND ALWAYS'}</span>
    <h1>{about ? <>One Platform.<br /><span>Every Generation.</span><small className="about-hero-line">Better Health Management.</small></> : <>Complete Healthcare<br />for <span>Every Stage of Life</span></>}</h1>
    <p>{about ? 'From little beginnings to new chapters, every family deserves care that understands them. Better health management, built around the people who matter most.' : 'From your child’s first steps to women’s health and pregnancy care, to managing adult health and chronic conditions — FamilyCare+ brings thoughtful care to your entire family.'}</p><Benefits />{!about && <button className="button primary hero-start" onClick={() => openAccount()}>Get Started <ArrowRight size={17} /></button>}</div>
    <div className="hero-visual"><img src="/images/family.png" alt="Parents in blue and pink embracing their smiling daughter" fetchPriority="high" /><div className="hero-note">Healthy<br />Families<br />Happier<br />Tomorrows <Heart size={18} fill="currentColor" /></div><div className="floating-note"><span className="icon-circle"><Heart fill="currentColor" /></span><span>Thoughtful care for<br /><strong>your whole family.</strong></span></div></div>
  </section>;
}
function CareCard({ data }: { data: CareService }) {
  const Icon = data.icon;
  return <article className={`care-card ${data.theme}`}><div className="card-art" aria-hidden="true"><span className="art-orbit" /><span className="art-leaf leaf-one" /><span className="art-leaf leaf-two" /><span className="art-leaf leaf-three" /></div><img className="card-photo" src={data.image} alt={data.alt} />
    <div className="card-content"><span className="badge"><Icon size={16} fill="currentColor" />{data.label}</span><h2>{data.title}</h2><p>{data.short}</p><ul>{data.items.map(([Item, text]) => <li key={text}><span><Item size={17} /></span>{text}</li>)}</ul><Link className="button care-button" to={`/services#${data.id}`}>Explore {data.title}<ArrowRight size={18} /></Link></div><span className="card-note">{data.note}<Heart size={14} fill="currentColor" /></span>
  </article>;
}
export function CareGrid() { return <section id="care-options" className="care-grid" aria-label="Explore our care services">{care.map(data => <CareCard key={data.id} data={data} />)}</section>; }
export function TrustBar() {
  const items: IconText[] = [[ShieldCheck, 'Prevention & wellness', 'at every stage'], [Smartphone, 'Stay informed', 'as your family grows'], [Users, 'Care for', 'the whole family'], [Heart, 'Better Care', 'Brighter Tomorrows']];
  return <section className="trust-bar"><div className="trust-intro"><span className="mini-logo"><Users /></span><div><strong>One Platform<br />for Your Family’s Health</strong><small>Every stage. Every generation. Together.</small></div></div>{items.map(([Icon, a, b]) => <div className="trust-item" key={a}><span className="icon-circle"><Icon /></span><small>{a}<br />{b}</small></div>)}</section>;
}
export function Footer() {
  return <footer className="site-footer"><div className="footer-introduction"><Logo /><p>One place for every generation.<br />Care for today, tomorrow and always.</p><span className="demo-badge">PLATFORM IN DEVELOPMENT</span></div><div className="footer-column"><strong>Explore</strong><Link to="/">Home</Link><Link to="/about">About Us</Link><Link to="/services">Our Services</Link><Link to="/for-doctors">For Doctors</Link></div><div className="footer-column"><strong>Care areas</strong><Link to="/services/child-care">Child Care</Link><Link to="/services/womens-health">Women’s Health</Link><Link to="/services/adult-health">Adult Health</Link></div><div className="footer-column"><strong>Here to help</strong><Link to="/contact">Contact & Support</Link><Link to="/#faq">Frequently Asked Questions</Link><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link></div><div className="footer-bottom"><span>© {new Date().getFullYear()} FamilyCare+.</span><span>Interactive public preview · no live clinical service or emergency care.</span></div></footer>;
}
