import { Link, useLocation } from 'react-router-dom';
import { DoctorSection, FinalCTA } from '../components/Sections';

export default function Information() {
  const { pathname } = useLocation();
  if (pathname === '/for-doctors') return <><section className="services-page-heading"><span className="eyebrow">FOR DOCTORS</span><h1>More context.<br /><span>More connected care.</span></h1><p>A separate professional journey for verified, patient-authorized care.</p></section><DoctorSection /><FinalCTA /></>;
  const content = pathname === '/privacy' ? {
    title: 'Privacy in this preview',
    text: 'This public website demonstrates planned health-management features. It has no patient database, medical-record uploads, active account registration or authorized doctor access. Dashboard profiles and readings are fictional.',
    detail: 'Preview selections and reminder switches are held in temporary page state. They reset when the page reloads and do not send notifications. Images are served from project assets; Google Fonts may receive standard font requests from your browser. A full privacy policy and verified access controls are required before live health-data collection.',
  } : pathname === '/terms' ? {
    title: 'About using this preview',
    text: 'FamilyCare+ is in development. This website presents the product concept and does not currently provide medical consultations, appointment booking, vaccine scheduling, diagnosis or treatment.',
    detail: 'Sample health readings and timelines are illustrative. They are not personal medical guidance. Account registration, doctor verification, real notifications and medical-record storage are not available here. Final service terms will be published before launch.',
  } : {
    title: 'Contact & support',
    text: 'FamilyCare+ is in development. Verified support contact details and service hours have not been published yet. We will add them here when the service is ready.',
    detail: 'For questions about the product concept, explore the FAQ and service pages. This preview cannot accept patient reports, contact requests, appointment bookings or urgent medical requests.',
  };
  return <section className="content-section information-page"><span className="eyebrow">FAMILYCARE+ · PUBLIC PREVIEW</span><h1>{content.title}</h1><p>{content.text}</p><p>{content.detail}</p><div><Link className="button primary" to="/#faq">Read the FAQ</Link><Link className="button outline" to="/services">Explore services</Link></div></section>;
}
