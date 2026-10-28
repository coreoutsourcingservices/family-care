'use client';
import {useUiTranslation as useTranslation} from '@/lib/i18n';
export default function ErrorPage({reset}:{reset:()=>void}) {const {t}=useTranslation();return <main className="standalone"><div className="empty-card"><h1>{t('We could not load this page')}</h1><p>{t('The service may be temporarily unavailable. Please try again.')}</p><button className="primary" onClick={reset}>{t('Try again')}</button></div></main>;}
