# Pregnancy Care Guide

Base: `http://127.0.0.1:5001/api/v1/women`

## Preview guide from frontend month/week

`POST /pregnancy-guide` — authenticated PATIENT or DOCTOR. Does not save a pregnancy or create a notification.

```json
{"month":5}
```

Alternatively `{"week":20}`. Supply exactly one integer: month 1–9 or week 1–42. Months use approximate ranges, not a clinical gestational-age calculation. Response `guide` includes week/month/trimester, food, daily care, checkups, urgent warning signs, source links and disclaimer.

## Save stage and opt into weekly notices

`PUT /profiles/{profile_id}/pregnancy-care` — primary Women profile user only.

```json
{"month":5,"as_of_date":"2026-11-02","active":true,"version":0}
```

Use today's local date instead of this sample date. This saves the stage in PostgreSQL. The week advances from `as_of_date`. `version:0` creates settings; updates must send the returned version. Stale updates return 409. Invalid input returns 422. Future as-of dates are rejected.

`GET /profiles/{profile_id}/pregnancy-care` — profile owner or an unexpired connected recipient with pregnancy-tab view access. Returns `settings` and `guide`; before setup both are null. An inactive guide is null. No doctor or family delegate can change the primary user's stage or notification preference.

Set `active:false` with the current stage and version to stop guide notices. A stage beyond 42 weeks requires review and stops new weekly notices; the app does not infer delivery or postpartum status.

## Notifications and frontend

Notification type `pregnancy_guide`, title **Pregnancy Care Guide**, data `{profile_id,module:"women",area:"pregnancy_guide"}`. The primary profile user's inbox receives a generic notice on activation and each new calculated week. The background scanner runs approximately every minute, with idempotent event keys. Notifications link to Pregnancy care, where authorised users can view the guide. No pregnancy details are sent in browser-alert bodies.

Cookie clients use the existing patient cookie, `X-FamilyCare-Portal: patient`, `X-Requested-With: FamilyCare`, and CSRF header. Bearer clients use `Authorization: Bearer <access_token>`.

## Sources and clinical limits

Content is FamilyCare educational adaptation, **not WHO endorsement or individual medical advice**. Food guidance is general across pregnancy; month/week organises trimester focus and contact milestones, not a different diet prescription for every month. Medications and supplement doses are not prescribed by this endpoint.

- [WHO antenatal care recommendations](https://www.who.int/publications/i/item/9789241549912)
- [WHO eight-contact schedule](https://www.who.int/news/item/07-11-2016-new-guidelines-on-antenatal-care-for-a-positive-pregnancy-experience)
- [WHO physical activity guidelines](https://www.who.int/publications/i/item/9789240015128)
- [WHO pregnancy warning signs](https://www.who.int/campaigns/world-health-day/2025/key-messages)
- [WHO food safety](https://www.who.int/activities/promoting-safe-food-handling/five-key-to-safer-food)

Sources checked 2026-11-02. Clinician advice and local care protocols take precedence; warning symptoms require urgent care, not waiting for this app.
