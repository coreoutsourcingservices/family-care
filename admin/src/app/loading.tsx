'use client';
import {useUiTranslation as useTranslation} from '@/lib/i18n';
export default function Loading(){const {t}=useTranslation();return <main className="standalone"><p role="status">{t('Loading Familycare…')}</p></main>;}
