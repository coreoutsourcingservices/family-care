export type Role = 'ADMIN' | 'SUPERADMIN';
export type ProfileCounts={total:number;members:number;self:number;child:number;adult:number;women:number};
export type User = {profile_counts?:ProfileCounts;id: string; public_id: string; full_name: string; email: string; phone_number?: string; referral_id?: string; referred_doctor?: {referral_id:string; public_id:string; full_name:string; email:string; mobile_number?:string} | null; role: string; approval_status: string; account_status: string; email_verified: boolean; doctor?: {qualification: string; specialization?: string; medical_registration_number: string; registering_council: string; verification_status: string}};
export type PageData = {items: User[]; total: number; page?: number; per_page?: number};
export const rolePath = (role: Role) => role === 'SUPERADMIN' ? '/superadmin' : '';
export const apiRole = (role: Role) => role === 'SUPERADMIN' ? 'superadmin' : 'admin';
