'use client';
import {useUiTranslation} from '@/lib/i18n';
export default function LocalizedText({text}:{text:string}){const {t}=useUiTranslation();return <>{t(text)}</>;}
