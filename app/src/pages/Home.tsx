import { Hero, CareGrid, TrustBar } from '../components/Website';
import { WhyFamilyCare, HowItWorks, PlatformPreview, FamilyProfiles, DoctorSection, ReminderPreview, FAQ, FinalCTA } from '../components/Sections';

export default function Home() {
  return (
    <>
      <Hero />
      <CareGrid />
      <TrustBar />
      <WhyFamilyCare />
      <HowItWorks />
      <PlatformPreview />
      <FamilyProfiles />
      <DoctorSection />
      <ReminderPreview />
      <FAQ />
      <FinalCTA />
    </>
  );
}
