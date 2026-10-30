export type DoctorSetupDetails = {
  images?: Partial<Record<'profile_photo' | 'degree_photo', { name: string; url: string }>>;
  qualification: string | null;
  medical_registration_number: string | null;
  registering_council: string | null;
  specialization: string | null;
  nmr_id: string | null;
  address: string | null;
  clinic_address: string | null;
  years_of_experience: number | null;
};

export type DoctorAuthFields = {
  notification_token?: string;
  requires_profile_setup?: boolean;
  setup_token?: string;
  doctor?: DoctorSetupDetails;
  rejection_reason?: string | null;
};

export type DoctorAuthOutcome = 'setup' | 'approval' | 'session';
