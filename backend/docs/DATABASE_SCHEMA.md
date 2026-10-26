# Identity database

All tables are in private `familycare`; no new objects are added to Supabase Auth/public.
UUIDs are stored as PostgreSQL UUID columns and serialized as strings. Python generates
UUID4 keys. Business IDs are generated only by a PostgreSQL trigger with independent
sequences. Sequences are concurrency-safe, may have gaps and never reuse deleted IDs.
IDs expand after six digits (e.g. C1000000). Trigger blocks role/public ID mutation.

| Table | Purpose / important relationships |
|---|---|
| users | Unique normalized email, UUID/public ID, role, Argon2id hash, verification/approval/active flags |
| admin_profiles | One-to-one users |
| doctor_profiles | Qualification/council/registration; unique council+registration, optional unique NMR ID; reviewer |
| patient_profiles | One-to-one users |
| otp_challenges | User/purpose, HMAC code hash, attempts, created/expiry/consumed timestamps |
| approval_requests | One current request per applicant; pending/reviewed status and reviewer/reason |
| user_sessions | User, transport, CSRF hash, expiration and revocation |
| refresh_tokens | Hashed opaque refresh credential linked to session (session is token family) |
| password_reset_events | User + consumed reset challenge |
| email_notifications | Durable outbox, template/context, optional OTP challenge, attempt/delivery state |
| audit_logs | Actor/target/action/timestamp; no credentials or OTPs |

Canonical DDL: `supabase/0001_identity.sql`; ORM definitions: `core/models.py`.
All timestamps use UTC `timestamp without time zone`. Python serializes listed dates
with a trailing Z; do not interpret database values as local wall time.

State transitions:

```text
registration -> PENDING_EMAIL_VERIFICATION
email OTP verified (patient) -> APPROVED -> JWT session
email OTP verified (admin/doctor) -> PENDING_APPROVAL
review -> APPROVED or REJECTED
rejected doctor resubmission -> PENDING_APPROVAL (audit preserves prior decision events)
account suspension -> SUSPENDED + all sessions revoked
reactivation -> ACTIVE (approval flag unchanged, old sessions remain revoked)
```

Approval dashboard requests are persisted in `approval_requests`. This release uses
polling list endpoints rather than realtime push. Audit rows store decision events;
current rejection details live on the request. Attachments/certificates are not accepted
by this release; no upload API is exposed. Reviewers inspect submitted registration
fields; professional medical verification remains an external review responsibility.

All write workflows use transactions. User-first row locking serializes OTP issuance,
verification, password changes and refresh. Refresh then locks session/token in a
consistent order; invalid reuse revokes its session. OTP errors explicitly commit the
failed-attempt count. Outbox enqueue participates in registration/approval transactions.
Indexes cover unique IDs/emails, roles/approval status, sessions, challenge user lookup,
pending mail status/scheduling and audit time/action. Profiles and results are paginated.

No appointments, clinical notes, prescriptions or billing tables are included.
