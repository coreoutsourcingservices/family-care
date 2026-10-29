-- Family Care identity schema. Run on an empty familycare schema. Existing public/auth tables are preserved.

CREATE SCHEMA IF NOT EXISTS familycare;

REVOKE ALL ON SCHEMA familycare FROM PUBLIC;

DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='anon') THEN EXECUTE 'REVOKE ALL ON SCHEMA familycare FROM anon'; END IF; IF EXISTS (SELECT FROM pg_roles WHERE rolname='authenticated') THEN EXECUTE 'REVOKE ALL ON SCHEMA familycare FROM authenticated'; END IF; END $$;

CREATE SEQUENCE familycare.admin_id_seq;

CREATE SEQUENCE familycare.doctor_id_seq;

CREATE SEQUENCE familycare.patient_id_seq;


CREATE TABLE familycare.users (
	id UUID NOT NULL,
	public_id VARCHAR(40) NOT NULL,
	username VARCHAR(80),
	full_name VARCHAR(120) NOT NULL,
	email VARCHAR(254) NOT NULL,
	phone_number VARCHAR(20),
	password_hash TEXT NOT NULL,
	role VARCHAR(20) NOT NULL,
	email_verified BOOLEAN NOT NULL,
	approval_status VARCHAR(32) NOT NULL,
	account_status VARCHAR(16) NOT NULL,
	must_change_password BOOLEAN NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	last_login_at TIMESTAMP WITHOUT TIME ZONE,
	CONSTRAINT pk_users PRIMARY KEY (id),
	CONSTRAINT ck_users_role CHECK (role IN ('SUPERADMIN','ADMIN','DOCTOR','PATIENT')),
	CONSTRAINT ck_users_approval CHECK (approval_status IN ('PENDING_EMAIL_VERIFICATION','PENDING_APPROVAL','APPROVED','REJECTED')),
	CONSTRAINT ck_users_status CHECK (account_status IN ('ACTIVE','SUSPENDED')),
	CONSTRAINT uq_users_public_id UNIQUE (public_id),
	CONSTRAINT uq_users_username UNIQUE (username),
	CONSTRAINT uq_users_email UNIQUE (email)
)

;

CREATE INDEX ix_users_approval_status ON familycare.users (approval_status);

CREATE INDEX ix_users_role ON familycare.users (role);


CREATE TABLE familycare.admin_profiles (
	user_id UUID NOT NULL,
	CONSTRAINT pk_admin_profiles PRIMARY KEY (user_id),
	CONSTRAINT fk_admin_profiles_user_id_users FOREIGN KEY(user_id) REFERENCES familycare.users (id) ON DELETE CASCADE
)

;


CREATE TABLE familycare.approval_requests (
	id UUID NOT NULL,
	applicant_id UUID NOT NULL,
	applicant_role VARCHAR(20) NOT NULL,
	requested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	status VARCHAR(20) NOT NULL,
	reviewed_by UUID,
	reviewed_at TIMESTAMP WITHOUT TIME ZONE,
	rejection_reason VARCHAR(500),
	CONSTRAINT pk_approval_requests PRIMARY KEY (id),
	CONSTRAINT uq_approval_requests_applicant_id UNIQUE (applicant_id),
	CONSTRAINT fk_approval_requests_applicant_id_users FOREIGN KEY(applicant_id) REFERENCES familycare.users (id) ON DELETE CASCADE,
	CONSTRAINT fk_approval_requests_reviewed_by_users FOREIGN KEY(reviewed_by) REFERENCES familycare.users (id)
)

;

CREATE INDEX ix_approval_requests_status ON familycare.approval_requests (status);


CREATE TABLE familycare.audit_logs (
	id UUID NOT NULL,
	actor_id UUID,
	target_id UUID,
	action VARCHAR(80) NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	CONSTRAINT pk_audit_logs PRIMARY KEY (id),
	CONSTRAINT fk_audit_logs_actor_id_users FOREIGN KEY(actor_id) REFERENCES familycare.users (id),
	CONSTRAINT fk_audit_logs_target_id_users FOREIGN KEY(target_id) REFERENCES familycare.users (id)
)

;

CREATE INDEX ix_audit_logs_action ON familycare.audit_logs (action);

CREATE INDEX ix_audit_logs_created_at ON familycare.audit_logs (created_at);


CREATE TABLE familycare.doctor_profiles (
	user_id UUID NOT NULL,
	qualification VARCHAR(200),
	specialization VARCHAR(200),
	medical_registration_number VARCHAR(100) NOT NULL,
	registering_council VARCHAR(200) NOT NULL,
	nmr_id VARCHAR(100),
	verification_status VARCHAR(32) NOT NULL,
	approved_by UUID,
	approved_at TIMESTAMP WITHOUT TIME ZONE,
	CONSTRAINT pk_doctor_profiles PRIMARY KEY (user_id),
	CONSTRAINT uq_doctor_profiles_registering_council UNIQUE (registering_council, medical_registration_number),
	CONSTRAINT fk_doctor_profiles_user_id_users FOREIGN KEY(user_id) REFERENCES familycare.users (id) ON DELETE CASCADE,
	CONSTRAINT uq_doctor_profiles_nmr_id UNIQUE (nmr_id),
	CONSTRAINT fk_doctor_profiles_approved_by_users FOREIGN KEY(approved_by) REFERENCES familycare.users (id)
)

;


CREATE TABLE familycare.otp_challenges (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	purpose VARCHAR(32) NOT NULL,
	code_hash VARCHAR(64),
	attempts INTEGER NOT NULL,
	consumed_at TIMESTAMP WITHOUT TIME ZONE,
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	CONSTRAINT pk_otp_challenges PRIMARY KEY (id),
	CONSTRAINT ck_otp_challenges_purpose CHECK (purpose IN ('verify_email','login','reset_password','change_password')),
	CONSTRAINT fk_otp_challenges_user_id_users FOREIGN KEY(user_id) REFERENCES familycare.users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_otp_challenges_user_id ON familycare.otp_challenges (user_id);


CREATE TABLE familycare.patient_profiles (
	user_id UUID NOT NULL,
	CONSTRAINT pk_patient_profiles PRIMARY KEY (user_id),
	CONSTRAINT fk_patient_profiles_user_id_users FOREIGN KEY(user_id) REFERENCES familycare.users (id) ON DELETE CASCADE
)

;


CREATE TABLE familycare.user_sessions (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	transport VARCHAR(10) NOT NULL,
	csrf_hash VARCHAR(64),
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	revoked_at TIMESTAMP WITHOUT TIME ZONE,
	CONSTRAINT pk_user_sessions PRIMARY KEY (id),
	CONSTRAINT fk_user_sessions_user_id_users FOREIGN KEY(user_id) REFERENCES familycare.users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_user_sessions_user_id ON familycare.user_sessions (user_id);


CREATE TABLE familycare.email_notifications (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	challenge_id UUID,
	template VARCHAR(40) NOT NULL,
	context_json TEXT NOT NULL,
	status VARCHAR(16) NOT NULL,
	attempts INTEGER NOT NULL,
	available_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	sent_at TIMESTAMP WITHOUT TIME ZONE,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	CONSTRAINT pk_email_notifications PRIMARY KEY (id),
	CONSTRAINT fk_email_notifications_user_id_users FOREIGN KEY(user_id) REFERENCES familycare.users (id) ON DELETE CASCADE,
	CONSTRAINT fk_email_notifications_challenge_id_otp_challenges FOREIGN KEY(challenge_id) REFERENCES familycare.otp_challenges (id)
)

;

CREATE INDEX ix_email_notifications_available_at ON familycare.email_notifications (available_at);

CREATE INDEX ix_email_notifications_status ON familycare.email_notifications (status);

CREATE INDEX ix_email_notifications_user_id ON familycare.email_notifications (user_id);


CREATE TABLE familycare.password_reset_events (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	challenge_id UUID NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	CONSTRAINT pk_password_reset_events PRIMARY KEY (id),
	CONSTRAINT fk_password_reset_events_user_id_users FOREIGN KEY(user_id) REFERENCES familycare.users (id) ON DELETE CASCADE,
	CONSTRAINT fk_password_reset_events_challenge_id_otp_challenges FOREIGN KEY(challenge_id) REFERENCES familycare.otp_challenges (id)
)

;

CREATE INDEX ix_password_reset_events_user_id ON familycare.password_reset_events (user_id);


CREATE TABLE familycare.refresh_tokens (
	id UUID NOT NULL,
	session_id UUID NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	consumed_at TIMESTAMP WITHOUT TIME ZONE,
	CONSTRAINT pk_refresh_tokens PRIMARY KEY (id),
	CONSTRAINT fk_refresh_tokens_session_id_user_sessions FOREIGN KEY(session_id) REFERENCES familycare.user_sessions (id) ON DELETE CASCADE,
	CONSTRAINT uq_refresh_tokens_token_hash UNIQUE (token_hash)
)

;

CREATE INDEX ix_refresh_tokens_session_id ON familycare.refresh_tokens (session_id);


CREATE FUNCTION familycare.assign_public_id() RETURNS trigger
LANGUAGE plpgsql SET search_path = '' AS $$
DECLARE n bigint; prefix text;
BEGIN
  IF TG_OP = 'UPDATE' THEN
    IF NEW.public_id IS DISTINCT FROM OLD.public_id OR NEW.role IS DISTINCT FROM OLD.role THEN
      RAISE EXCEPTION 'Public ID and role are immutable';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.role = 'SUPERADMIN' THEN
    IF NEW.username IS DISTINCT FROM 'superadmin' THEN RAISE EXCEPTION 'Invalid bootstrap username'; END IF;
    NEW.public_id := 'superadmin';
    RETURN NEW;
  END IF;
  IF NEW.public_id IS NOT NULL THEN RAISE EXCEPTION 'Public ID must be database generated'; END IF;
  CASE NEW.role
    WHEN 'ADMIN' THEN prefix := 'A'; n := nextval('familycare.admin_id_seq');
    WHEN 'DOCTOR' THEN prefix := 'D'; n := nextval('familycare.doctor_id_seq');
    WHEN 'PATIENT' THEN prefix := 'C'; n := nextval('familycare.patient_id_seq');
    ELSE RAISE EXCEPTION 'Invalid role';
  END CASE;
  NEW.public_id := prefix || lpad(n::text, greatest(6, length(n::text)), '0');
  RETURN NEW;
END;
$$;
CREATE TRIGGER assign_public_id BEFORE INSERT OR UPDATE ON familycare.users
FOR EACH ROW EXECUTE FUNCTION familycare.assign_public_id();
REVOKE ALL ON ALL TABLES IN SCHEMA familycare FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA familycare FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA familycare FROM PUBLIC;
DO $$
BEGIN
 IF EXISTS (SELECT FROM pg_roles WHERE rolname='anon') THEN
  EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA familycare FROM anon';
 END IF;
 IF EXISTS (SELECT FROM pg_roles WHERE rolname='authenticated') THEN
  EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA familycare FROM authenticated';
 END IF;
END $$;
