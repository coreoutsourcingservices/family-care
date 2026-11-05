# Admin Recycle Bin and Recent Activity

The admin sidebar has `/recycle-bin` and `/recent-activity`. Access is restricted to authenticated active administrators. Recycle Bin exposes item type, who deleted it, deletion time and expiry; it never exposes medical report filenames, medical content, diary values or private note contents. Administrators can restore eligible content without obtaining permission to read it.

For newly deleted content, the application retains a recoverable copy for 30 days. This covers care profiles, reports and their OCR results, imported child records, child/adult/women records, profile planner notes/tasks, personal notes, and removed or replaced doctor onboarding images. An image is restored only if its slot is empty. Restoring a report also restores its linked imported records; other deleted profile content requires its profile to be restored first. Entries deleted before this feature was installed cannot be recovered unless still available through another backup.

Session revocation, revoked access grants, doctor disconnection, invitations and push-subscription removal apply immediately and are not reversible recycle-bin items. This prevents restoring deleted content from silently re-enabling revoked credentials or sharing grants. Profile removal keeps an invited member restricted to that profile during retention; permanent removal suspends that member account and revokes its sessions.

The cleanup worker checks every 15 minutes. After expiry, restore is rejected and the worker removes database content and any authenticated Cloudinary asset. Failed storage/database removals remain pending and retry after an hour; actual purge can occur after the expiry time if a worker or storage service is unavailable. The local `server.py` starts the worker. WSGI starts it in each serving process with database row locking; production operators should also run `python -m scripts.recycle_worker` as a supervised service to guarantee cleanup during inactive periods and across process restarts. `python -m scripts.recycle_worker --once` runs one cleanup pass. Never run this on a production database as a test.

Apply `python -m alembic upgrade head` before starting the updated API. Migration `0028_recycle_bin` does not backfill existing deleted records or immediately purge them.

## API

- `GET /api/v1/admin/recycle-bin?page=1&per_page=20` returns `{items,total,page,per_page}`. Each item includes `id`, `type`, `label`, `actor`, `deleted_at`, `expires_at`, `expired`, and `requires_report`. Expired items await permanent cleanup and cannot be restored.
- `POST /api/v1/admin/recycle-bin/{id}/restore` returns `{"message":"Item restored"}`; 404 means not found and 409 means expired, unavailable, or a parent/report must be restored first. Restores are audited.
- `GET /api/v1/admin/recent-activity?page=1&per_page=20&action=registered` returns filtered, paginated administrative activity. `action` is optional; allowed values are `registered`, `care_profile_created`, `care_profile_updated`, `login_success`, `approval_approved`, `approval_rejected`, `account_suspended`, `account_active`, `care_profile_removed`, `care_report_deleted`, `child_record_removed`, `doctor_vaccination_removed`, `women_diary_removed`, `planner_deleted`, `customer_note_deleted`, `doctor_profile_photo_removed`, `recycle_item_restored`, `recycle_item_purged`. This endpoint intentionally excludes private clinical data and superadmin-only audit history.
- The activity endpoint accepts `period=7d`, `1m`, `1y`, `all` (default), or `custom`. Presets are rolling periods; a month and year use calendar arithmetic. For `custom`, supply `start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`; both calendar dates are inclusive in Asia/Kolkata. Invalid periods, missing dates or reversed ranges return HTTP 400. Date and activity filters apply before pagination.

Admin web clients use the existing admin portal cookie/CSRF proxy; API clients can use the admin bearer token. Recent Activity entries come from the real audit log, not sample data.


### Delete filtered activity history
GET `/api/v1/admin/recent-activity` returns `delete_token` for the exact selected period and activity type across all pages. POST `/api/v1/admin/recent-activity/delete` with `{"token":"<delete_token>","confirmed":true}` moves matching activity entries into Recycle Bin for 30 days. The short-lived selection belongs to the requesting admin. A changed selection returns 409; refresh before confirming again. This operation does not delete patient accounts or medical records. The admin UI shows a Cancel / Delete confirmation dialog with the selected range and count.


### Empty Recycle Bin immediately
The admin Delete All button shows a Cancel / Delete All dialog with the total count across all pages and a permanent deletion warning. GET `/api/v1/admin/recycle-bin` supplies a short-lived `delete_token`. POST `/api/v1/admin/recycle-bin/empty` with `{"token":"<delete_token>","confirmed":true}` permanently deletes the confirmed contents, including items still within 30 days. A changed selection returns 409. The response includes `deleted` and `failed`; failed storage deletions retain their markers for retry. New items arriving after confirmation are excluded. This action cannot be restored.


### Super Admin
`GET /api/v1/superadmin/audit-logs` supports the same period/action/custom date parameters and includes `actor_name`, `target_name`, and the existing actor/target IDs for API compatibility. Deleted events are excluded. `POST /api/v1/superadmin/audit-logs/delete` uses the same confirmed token flow. Super Admin can manage the full recycle bin through `/api/v1/superadmin/recycle-bin`, `/<id>/restore`, and `/empty`. History deleted through Super Admin is hidden from the ordinary Admin recycle bin and cannot be restored or purged by Admin. Tokens are bound to their user and portal.
