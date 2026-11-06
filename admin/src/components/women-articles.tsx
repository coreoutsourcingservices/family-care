'use client';
import WomenArticleManager from '../../../app/src/components/WomenArticleManager';
import {api} from '@/lib/api';
export default function WomenArticles(){return <WomenArticleManager request={api}/>;}
