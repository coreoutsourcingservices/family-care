# Age-based child vaccination plans

Admin and superadmin add a vaccine, then a dose schedule with a name, guideline,
instructions, age unit and start/end age. New schedules default to `active: true`
and `child_visible: true`. For six calendar months use `age_unit: "months"`,
`age_start: 6`, `age_end: 6`. A child born 2026-01-31 sees 2026-07-31.
Calendar month ends are clamped, not approximated as 30 days.

## Availability

`PATCH /api/v1/admin/vaccination/schedules/{schedule_id}/visibility`

Superadmin uses `/api/v1/superadmin/vaccination/schedules/{schedule_id}/visibility`.
Use the corresponding role's bearer token or authenticated cookie with CSRF.

Request:
```json
{"active": true, "child_visible": true}
```

Response 200:
```json
{"schedule":{"id":"<UUID>","status":"DRAFT","active":true,"child_visible":true}}
```
The actual response contains the complete schedule. `active: false` hides the
version. Retired versions return 409; unauthorized roles return 403; missing
versions return 404; invalid bodies return 422. Existing imported drafts default
to visible unless explicitly disabled. Published versions are
visible by default; this endpoint can deactivate and reactivate them.

`PUT /api/v1/admin/vaccination/vaccines/{vaccine_id}` (or superadmin equivalent)
accepts the full vaccine body including `active`. Deactivating the catalog entry
hides all its doses without deleting saved vaccination history.

## Child and doctor reads

- Parent: `GET /api/v1/children/{child_id}/vaccinations?schedule_type=UIP&view=all`
- Connected doctor: `GET /api/v1/doctors/care-profiles/{child_id}/vaccination-plan`
  returns the identical child-specific timeline under `UIP` and `IAP`.

Each dose includes `recommended_date`, `window_end`, `publication_status`,
`status`, `display_status`, `instructions`, `vaccine` and source details.
An active unpublished entry has `publication_status: "DRAFT"` (or `IN_REVIEW`,
`APPROVED`) and `status: "REVIEW_REQUIRED"`. It is labelled Doctor Review and
does not send vaccination-due reminders. Activation does not attest to clinical
review. Reviewed, published doses retain the existing reminder/eligibility flow.
An active published version takes precedence over a pending version of the same
vaccine/dose. Refresh the child or doctor page after changing availability.

This is a vaccination plan feature. Medicine prescriptions and their dosage
remain separate doctor workflows.

The connected doctor can use `POST /api/v1/doctors/care-profiles/{child_id}/vaccination-plan`
with `schedule_id`, `decision: "NOT_APPLICABLE"`, substantive `notes` (20+ characters)
and `attestation: true` to deactivate applicability for this child only. `CONFIRM`
restores applicability after parent location/history are recorded. An unpublished
entry still requires schedule medical review even after individual confirmation.
Doctor actions never change other children's plans or the global catalog.
