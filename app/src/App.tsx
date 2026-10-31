import { lazy, Suspense, useEffect, useRef } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { gsap } from 'gsap';
import { Header, Footer } from './components/Website';
import Home from './pages/Home';
import { AcceptFamilyInvitation } from './components/FamilyInvitations';
import CustomerNotifications from '../../customer/src/notifications/CustomerNotifications';
import AboutUs from './pages/AboutUs';
import Services, { CareDetailsPage } from './pages/Services';
import Information from './pages/Information';
import AuthPage from './pages/auth/AuthPage';
import CustomerDashboard from './pages/CustomerDashboard';
const ChildDashboard = lazy(() => import('../../customer/src/modules/child/ChildDashboard'));
const AdultDashboard = lazy(() => import('../../customer/src/modules/adult/AdultDashboard'));
const WomenDashboard = lazy(() => import('../../customer/src/modules/women/WomenDashboard'));
import AccessApprovals from './pages/AccessApprovals';
const DoctorRoutes = lazy(() => import('../../doctor/src/DoctorRoutes'));

export default function App() {
  const location = useLocation();
  const isAuth = /^\/(customer|doctor)\/(signup|login)$/.test(location.pathname);
  const isCustomerDashboard = ['/customer/approvals', '/customer/dashboard', '/customer/child', '/customer/women', '/customer/adult', '/doctor/dashboard','/doctor/vaccination-reviews'].includes(location.pathname);
  const isChildSpace = /^\/customer\/child\/[^/]+/.test(location.pathname);
  const isWomenSpace=location.pathname.startsWith('/customer/women');
  const standalone = location.pathname.startsWith('/doctor/') || isAuth || isCustomerDashboard || isChildSpace || isWomenSpace || location.pathname.startsWith('/customer/adult');
  const mainRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const titles: Record<string, string> = {
      '/': 'Care for Every Stage of Life', '/about': 'About Us', '/services': 'Our Services',
      '/services/child-care': 'Child Care', '/services/womens-health': 'Women’s Health',
      '/services/adult-health': 'Adult Health', '/for-doctors': 'For Doctors',
      '/customer/signup': 'Customer Sign Up', '/customer/login': 'Customer Login',
      '/customer/dashboard': 'Your Family Dashboard',
      '/customer/child': 'Child Care', '/customer/women': "Women\u2019s Health", '/customer/adult': 'Adult Health',
      '/doctor/dashboard': 'Doctor Dashboard',
      '/doctor/setup-account': 'My Doctor Profile',
      '/doctor/patients': 'Patients', '/doctor/consultations': 'Consultations',
      '/doctor/child-care': 'Child Care', '/doctor/vaccination':'Vaccination Plans', '/doctor/clinical-records': 'Clinical Records', '/doctor/appointments': 'Appointments',
      '/doctor/prescriptions': 'Prescriptions', '/doctor/reports': 'Reports',
      '/doctor/settings': 'Doctor Settings', '/doctor/vaccination-reviews': 'Vaccination Reviews',
      '/customer/approvals': 'Access Approvals',
      '/customer/family-invite': 'Family Invitation',
      '/doctor/signup': 'Doctor Registration', '/doctor/login': 'Doctor Login',
      '/contact': 'Contact & Support', '/privacy': 'Preview Privacy', '/terms': 'Preview Terms',
    };
    document.title = `${titles[location.pathname] ?? (location.pathname.startsWith('/doctor/patients/')?'Patient overview':isChildSpace ? 'Child Care' : isWomenSpace ? 'Women?s Health' : location.pathname.startsWith('/customer/adult') ? 'Adult Health' : 'Page Not Found')} | FamilyCare+`;
    if (location.hash) requestAnimationFrame(() => document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({ behavior: 'instant' }));
    else window.scrollTo(0, 0);
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      const context = gsap.context(() => {
        if (mainRef.current?.querySelector('.hero-copy, .services-page-heading')) gsap.from('.hero-copy > *, .services-page-heading > *', { y: 16, opacity: 0, duration: 0.6, stagger: 0.1, ease: 'power2.out', clearProps: 'all' });
        if (mainRef.current?.querySelector('.hero-visual')) gsap.from('.hero-visual', { opacity: 0, duration: 0.8, clearProps: 'all' });
        if (mainRef.current?.querySelector('.care-card')) gsap.from('.care-card', { y: 22, opacity: 0, duration: 0.6, delay: 0.2, stagger: 0.1, ease: 'power2.out', clearProps: 'all' });
      }, mainRef);
      return () => context.revert();
    });
    return () => media.revert();
  }, [location.pathname, location.hash]);
  return <div className={standalone ? 'auth-site-shell' : 'site-shell'}><a className="skip-link" href="#main-content">Skip to content</a>{!standalone && <Header />}<CustomerNotifications/><main id="main-content" ref={mainRef}><Routes><Route path="/customer/family-invite" element={<AcceptFamilyInvitation/>}/><Route path="/doctor/*" element={<Suspense fallback={<p role="status">Opening doctor workspace...</p>}><DoctorRoutes /></Suspense>} /><Route path="/customer/child/*" element={location.search.includes("add=1")?<CustomerDashboard module="child" />:<Suspense fallback={<p role="status">Opening Child Care...</p>}><ChildDashboard/></Suspense>} /><Route path="/customer/approvals" element={<AccessApprovals />} /><Route path="/customer/women/*" element={<Suspense fallback={<p role="status">Opening Women?s Health?</p>}><WomenDashboard/></Suspense>} /><Route path="/customer/adult/*" element={<Suspense fallback={<p role="status">Opening Adult Health...</p>}><AdultDashboard/></Suspense>} /><Route path="/customer/dashboard" element={<CustomerDashboard />} /><Route path="/customer/signup" element={<AuthPage key="customer-signup" role="customer" mode="signup" />} /><Route path="/customer/login" element={<AuthPage key="customer-login" role="customer" mode="login" />} /><Route path="/" element={<Home />} /><Route path="/about" element={<AboutUs />} /><Route path="/services" element={<Services />} /><Route path="/services/:area" element={<CareDetailsPage />} /><Route path="/for-doctors" element={<Information />} /><Route path="/contact" element={<Information />} /><Route path="/privacy" element={<Information />} /><Route path="/terms" element={<Information />} /><Route path="*" element={<section className="not-found"><h1>Page not found</h1><Link to="/" className="button primary">Back to Home</Link></section>} /></Routes></main>{!standalone && <Footer />}</div>;
}
