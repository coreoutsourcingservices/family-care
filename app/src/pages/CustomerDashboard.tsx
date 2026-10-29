import AccountDoctorConnection from '../components/AccountDoctorConnection';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, FileText, Heart, LogOut, ShieldCheck, Users } from 'lucide-react';
import { Logo } from '../components/Website';
import ModuleSelector, { type ModuleId } from '../components/ModuleSelector';
import ChildCare from '../../../customer/src/modules/child/ChildCare';
import WomenHealth from '../modules/women/WomenHealth';
import AdultHealth from '../modules/adult/AdultHealth';
import { ApiError, authApi, type AuthUser } from '../lib/authApi';
import { CustomerLanguageProvider, CustomerLanguageSelector, useCustomerLanguage } from '../../../customer/src/localization/CustomerLanguage';
import './customer-dashboard.css';

export default function CustomerDashboard({ module }: { module?: ModuleId }) {
  return module ? <DashboardContent module={module}/> : <CustomerLanguageProvider><DashboardContent/></CustomerLanguageProvider>;
}

function DashboardContent({ module }: { module?: ModuleId }) {
  const {t,language,direction}=useCustomerLanguage();
  const navigate = useNavigate();
  const [user, setUser] = useState<AuthUser>();
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    let active = true;
    setError('');
    authApi('/patients/me', undefined, 'GET').then(data => {
      if (!active) return;
      if (data.user?.role !== 'PATIENT') { navigate('/customer/login', { replace: true }); return; }
      setUser(data.user);
    }).catch(failure => {
      if (!active) return;
      if (failure instanceof ApiError && (failure.status === 401 || failure.status === 403)) navigate('/customer/login', { replace: true });
      else setError(failure instanceof Error ? failure.message : 'Unable to load your account. Please try again.');
    });
    return () => { active = false; };
  }, [attempt, navigate]);

  async function signOut() {
    if (signingOut) return;
    setSigningOut(true); setError('');
    try { await authApi('/auth/logout'); navigate('/customer/login', { replace: true }); }
    catch (failure) {
      if (failure instanceof ApiError && failure.status === 401) { navigate('/customer/login', { replace: true }); return; }
      setError(failure instanceof Error ? failure.message : 'Unable to sign out. Please try again.');
    } finally { setSigningOut(false); }
  }

  return <div lang={language} dir={direction} className={`customer-dashboard ${module ? 'customer-form-page' : ''} ${module === 'child' ? 'customer-child-form' : ''}`}>
    {module !== 'child' && module !== 'women' && <header className="customer-dashboard-header"><Logo tagline={t('Healthier Families. Brighter Tomorrows.')} /><nav className="customer-dashboard-nav" aria-label="Dashboard navigation"><Link to="/customer/dashboard">{t('Home')}</Link><Link to="/customer/dashboard#customer-services">{t('Services')}</Link><Link to="/customer/child">{t('My family')}</Link><Link to="/contact">{t('Support')}</Link></nav><div className="customer-account-actions">
      {!module && user && <CustomerLanguageSelector/>}{user && <><span className="customer-account-name">{user.full_name}</span><button type="button" disabled={signingOut} onClick={signOut}><LogOut size={16} />{t(signingOut ? 'Signing out...' : 'Sign out')}</button></>}
    </div></header>}
    {!user ? <section className="customer-session-status" aria-live="polite">
      {error ? <><p role="alert">{t(error)}</p><button type="button" onClick={() => setAttempt(previous => previous + 1)}>{t('Try again')}</button><Link to="/customer/login">{t('Back to Login')}</Link></> : <p>{t('Loading your family dashboard...')}</p>}
    </section> : <div className="customer-dashboard-body">
      {!module && <section className="customer-family-hero">
        <div className="customer-hero-copy"><span className="customer-hero-eyebrow">{t('YOUR FAMILY. YOUR CARE.')}</span><h1>{t('Healthcare for')} <em>{t('Every')}</em><br /><span>{t('Stage of Life')}</span></h1><p>{t('Simple. Personal. Together.')}<br />{t('A little care for everyone you love.')}</p><div className="customer-hero-trust"><ShieldCheck size={16} />{t('Your people. Their health. One place.')}</div></div>
        <div className="customer-hero-photo"><span className="customer-hero-heart heart-one"><Heart fill="currentColor" /></span><img src="/images/family.png" alt="A smiling family together" /><span className="customer-hero-heart heart-two"><Heart fill="currentColor" /></span></div>
      </section>}
      {error && <p className="customer-dashboard-error" role="alert">{t(error)}</p>}
      {!module&&<AccountDoctorConnection/>}{!module && <ModuleSelector selected={null} translate={t} onSelect={id => navigate(`/customer/${id}`)} />}
      {module && <section id="customer-module-content" className="customer-module-content">
        {module === 'child' ? <ChildCare key={`child-${user.id}`} accountId={user.id} /> : module === 'women' ? <WomenHealth key={`women-${user.id}`} accountId={user.id} /> : <AdultHealth key={`adult-${user.id}`} accountId={user.id} />}
      </section>}
      {!module && <><section className="customer-services" id="customer-services"><div className="customer-section-title"><h2>{t('A little care. A lot of peace of mind.')}</h2><p>{t('Everything important, close to the people who matter.')}</p></div><div className="customer-service-grid">
        <article><span><FileText size={23} /></span><div><h3>{t('Health records, together')}</h3><p>{t('Keep reports with the right family profile.')}</p></div></article>
        <article><span><Users size={23} /></span><div><h3>{t('Space for everyone')}</h3><p>{t('Separate profiles for every family member.')}</p></div></article>
        <article><span><Heart size={23} /></span><div><h3>{t('Keep loved ones close')}</h3><p>{t('Save guardian and emergency contacts.')}</p></div></article>
      </div></section>
      <section className="customer-support-banner"><span className="customer-support-icon"><Heart size={29} /></span><div><h2>{t('Here for your family.')}</h2><p>{t('A helping hand, whenever you need guidance.')}</p></div><Link to="/contact">{t('Contact support')}<ArrowRight size={16} /></Link></section></>}
    </div>}
    {module !== 'child' && module !== 'women' && <p className="customer-dashboard-footer">{t("Your family's health, together in one place.")}</p>}
  </div>;
}
