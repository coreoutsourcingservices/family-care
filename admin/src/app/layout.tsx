import type { Metadata } from 'next';
import './globals.css';
import LanguageProvider from '@/components/language-provider';
export const metadata: Metadata = {title:{default:'Familycare · Care management',template:'%s · Familycare'},description:'Familycare administration and care network management'};
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="en"><body><LanguageProvider>{children}</LanguageProvider></body></html>;}
