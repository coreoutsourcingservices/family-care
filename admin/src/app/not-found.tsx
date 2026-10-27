'use client';
import Link from 'next/link';
import {useUiTranslation as useTranslation} from '@/lib/i18n';
export default function NotFound(){const {t}=useTranslation();return <main className="standalone"><div className="empty-card"><p className="eyebrow">{t('404 / PAGE NOT FOUND')}</p><h1>{t('A little off the care path.')}</h1><p>{t('This page does not exist or has moved.')}</p><Link className="primary button" href="/">{t('Back to sign in')}</Link></div></main>;}
