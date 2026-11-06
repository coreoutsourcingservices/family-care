import WomenArticleManager from '../../../app/src/components/WomenArticleManager';
import {careApi} from '../../../app/src/lib/careApi';
import DoctorWorkspaceLayout from '../components/DoctorWorkspaceLayout';
const request=<T,>(path:string,options:RequestInit={})=>careApi<T>('/'+path,options.body?JSON.parse(String(options.body)):undefined,true,(options.method??'GET') as 'GET'|'POST'|'PUT');
export default function WomenHealthArticles(){return <DoctorWorkspaceLayout><WomenArticleManager request={request} doctor/></DoctorWorkspaceLayout>;}
