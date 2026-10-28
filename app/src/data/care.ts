import { Heart, ShieldCheck, Stethoscope, Baby, Syringe, ChartNoAxesCombined, Apple, ClipboardList, Activity, Droplets, Users, Flower2, Sprout } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export type IconText = [LucideIcon, string, string];
export interface CareService {
  id: string; theme: 'blue' | 'pink' | 'teal'; label: string; title: string;
  description: string; short: string; image: string; alt: string; icon: LucideIcon;
  items: [LucideIcon, string][]; detail: string; note: string;
}
export const care: CareService[] = [
  { id: 'child', theme: 'blue', label: '0 – 12 Years', title: 'Child Care', description: 'A healthy start. A happier tomorrow.', short: 'Complete care for your child’s healthy and happy future.', image: '/images/child.png', alt: 'A smiling child in blue holding a teddy bear', icon: Users,
    items: [[Syringe, 'Vaccination Schedule & Reminders'], [ChartNoAxesCombined, 'Growth & Development Tracking'], [Apple, 'Nutrition & Milestones'], [ClipboardList, 'Health Records'], [Stethoscope, 'Doctor Consultations']], detail: 'From first vaccinations to everyday questions, explore support for children aged 0–12. Understand age-appropriate vaccination schedules, growth milestones, nutrition and preventive pediatric care.', note: 'Healthy\nBeginnings' },
  { id: 'women', theme: 'pink', label: 'All Life Stages', title: 'Women’s Health', description: 'Support for your own unique journey.', short: 'Support for every phase of your unique journey.', image: '/images/women.png', alt: 'An expectant mother in pink holding her baby bump', icon: Heart,
    items: [[Droplets, 'Menstrual Health Tracking'], [Baby, 'Pregnancy & Postnatal Care'], [Flower2, 'PCOS & Hormonal Issues'], [Heart, 'Gynecological Care'], [ShieldCheck, 'Screening & Preventive Care']], detail: 'Thoughtful care for women at every stage: menstrual concerns, pregnancy, recovery after birth and gynecological wellness. Explore support for PCOS, hormonal concerns and preventive screening.', note: 'Every Phase\nMatters' },
  { id: 'adult', theme: 'teal', label: '18+ Years', title: 'Adult Health', description: 'Stay healthy today. Stronger for tomorrow.', short: 'Stay healthy today and stronger for tomorrow.', image: '/images/adult.png', alt: 'A smiling adult man in a blue shirt with his arms crossed', icon: Users,
    items: [[Droplets, 'Diabetes Management'], [Activity, 'Blood Pressure Tracking'], [Heart, 'Cholesterol & Heart Health'], [Sprout, 'Lifestyle Guidance'], [ClipboardList, 'Regular Health Checkups']], detail: 'Make everyday health easier to understand. Explore care for high blood pressure, cholesterol and diabetes, alongside preventive checkups and guidance on nutrition and everyday habits.', note: 'Healthier Today\nStronger Tomorrow' },
];

