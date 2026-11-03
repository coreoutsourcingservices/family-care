import { Link, useLocation } from 'react-router-dom';
import { DoctorSection, FinalCTA } from '../components/Sections';

export default function Information() {
  const { pathname } = useLocation();
  if (pathname === '/for-doctors') return <><section className="services-page-heading"><span className="eyebrow">FOR DOCTORS</span><h1>More context.<br /><span>More connected care.</span></h1><p>A separate professional journey for verified, patient-authorized care.</p></section><DoctorSection /><FinalCTA /></>;
  const content = pathname === '/privacy' ? {
    title: 'Privacy and your information',
    text: 'FamilyCare stores account details, family profiles, health diaries, uploaded reports and sharing choices when you use these features. Private Women and Adult tabs require explicit access permissions. Review and revoke access in your profile.',
    detail: 'Original reports, extracted text and translations are separate. Review extracted values against the original before importing them. Translation uses the consent shown in the app. Deleted content is recoverable in Recycle Bin for up to 30 days unless an administrator permanently deletes it earlier. Restoring content does not restore revoked permissions.',
  } : pathname === '/terms' ? {
    title: 'Terms of use',
    text: 'Use your own credentials and provide accurate information. Manage family profiles only with authorization. Doctor accounts require approval. Self-entered readings, diaries and uploaded files do not establish a diagnosis or replace clinical review.',
    detail: 'A consultation request is separate from a confirmed appointment. Check its status and confirmed time. Medicine logs and draft prescriptions are separate from prescriptions issued by a doctor. Email and processing may be delayed; check delivery status and errors in the app.',
  } : {
    title: 'Contact & support',
    text: 'For account assistance, contact your FamilyCare organization administrator. Include the affected page and error message without passwords or OTPs.',
    detail: 'Share medical documents only through the authorized sharing controls. Support contact details and response hours are provided by your organization.',
  };
  return <section className="content-section information-page"><span className="eyebrow">FAMILYCARE+ · YOUR INFORMATION</span><h1>{content.title}</h1><p>{content.text}</p><p>{content.detail}</p><div><Link className="button primary" to="/#faq">Read the FAQ</Link><Link className="button outline" to="/services">Explore services</Link></div></section>;
}
