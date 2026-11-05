# Adult workspace: complete sample history

On 5 November 2026, the user's existing Adult self profile **Priyanshu Kishor** received 101 clearly labelled DEMO records, 12 private notes/tasks and six sample PDFs. Existing records, identity fields, connected doctors and sharing permissions were preserved.

## Coverage

Blood pressure: 24; glucose: 18; lipid panels: 6; medicine journal placeholders: 4; lifestyle: 24; preventive care: 8; medical history: 11 (including six fictional consultation notes); reminders: 6. Samples contain historical dated readings, completed tasks and upcoming reminders. Values are synthetic, schema-validated inputs and provide no diagnosis or medication instructions.

Consultation notes appear in the shared DoctorConsultation component's Saved consultation notes section. No appointment request or doctor approval was fabricated. Medicine examples use explicit DEMO placeholders, with no actual medicine prescribed. Settings and Access & Sharing retain real account values.

Six private report categories were uploaded through the normal authorized Adult report endpoint: Lab tests, Doctor report, Prescriptions, Scans, Vaccination, Others. The lab PDF was downloaded from the configured private Cloudinary storage and processed by the installed PaddleOCR runtime. Stored status: COMPLETED. Extracted values verified: glucose 94, total cholesterol 182, LDL 102, HDL 54, triglycerides 126. No external translation or automatic clinical import was requested. The scan placeholder is stored without interpretation.

## Files

- Data generator: `backend/scripts/adult_demo_history.py`
- Explicit target importer: `backend/scripts/seed_adult_history.py --profile-id UUID`
- PDF samples, synthetic browser fixture and real OCR output: `app/public/demo/adult/`

The importer skips existing per-profile IDs and sample report filenames, validates AdultInput payloads and records edit revisions. Notes/tasks are private to the primary account. Existing personal records are not edited. Repeating the import does not duplicate samples.

## Fix and verification

The Adult shared-report upload route inherited the 16 KB general request limit. It now uses the existing authorized report controller and its 10 MB file limit and multipart validation. Activating this backend source fix requires restarting the running backend through its normal launcher; the saved data and completed reading already exist in the database.

- `npm run build --workspace app`
- `node app/scripts/check-adult-history.mjs`: all 14 Adult sidebar pages, historical rows, reports, planner, consultation notes, mobile overflow and runtime checks using isolated synthetic API fixtures.
- `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_adult_history_demo.py -q`: schema coverage, idempotence, preservation of an existing personal entry, revisions, report upload and result visibility. Cloud transport/OCR are mocked in this regression; real cloud upload/download and OCR were separately executed for the selected account.

Next useful real inputs: verified readings/reports, actual clinician-provided medication details, emergency contacts and a real approved doctor's referral ID. Add or share these through the normal account controls.
