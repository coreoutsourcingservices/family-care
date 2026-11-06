'use client';
import WomenArticleManager from '../../../app/src/components/WomenArticleManager';
import {api} from '@/lib/api';
import {useUiTranslation} from '@/lib/i18n';
export default function WomenArticles(){const {t}=useUiTranslation();return <WomenArticleManager request={api} translateUi={value=>t(value)}/>;}
