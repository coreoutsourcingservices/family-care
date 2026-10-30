# FamilyCare+ public website

Shared React + TypeScript (TSX) website for customers and doctors. Includes `/`, `/about`, and `/services`, with responsive layouts inspired by the supplied design. Entry point: `src/main.tsx`.

Each route has its own page: `src/pages/Home.tsx`, `src/pages/AboutUs.tsx` and `src/pages/Services.tsx`. Routes are defined in `src/App.tsx`; shared navigation, footer and presentation components live in `src/components/Website.tsx`. Care content is in `src/data/care.ts`. Home presents the family hero and overview cards, About Us explains the family-care approach, and Services presents the detailed care categories without repeating the Home hero.

```powershell
cd app
npm install
npm run dev
```

Type check: `npm run typecheck`. Production build (includes type checking): `npm run build`. Preview: `npm run preview`.

Hosting must rewrite unknown paths to `index.html` for direct access to `/about` and `/services`.

Login, Sign Up and registration CTAs link to standalone customer/doctor authentication screens. Routes: `/customer/signup`, `/customer/login`, `/doctor/signup`, `/doctor/login`. The shared screen implementation and its responsive styles live in `src/pages/auth/AuthPage.tsx` and `auth.css`. Customer/Parent and Doctor selectors switch between the corresponding routes.

Both signup forms include name, Indian mobile number, email and password. Doctor signup's professional step contains only registration number and a required council dropdown, with no certificate upload. Email OTP, resend, login and reset requests use the existing backend. No demo OTP is built into the form. Remember me stores the email only; session credentials remain in HttpOnly cookies.

Doctor OTP verification and incomplete/rejected login responses open `/doctor/setup-account`, implemented in `doctor/src/pages/AccountSetup.tsx`. The verified name/email/mobile are read-only. Qualification, addresses, experience and optional specialization/NMR are collected there, then posted with the limited setup token to `/doctors/setup-profile`. Only a confirmed submission shows approval pending; only approved login sessions enter the dashboard. Setup tokens stay in memory and require a fresh login after reload/expiry. See `doctor/README.md` for the flow and checks.

Search filters the three care areas. For Doctors and Contact have dedicated informational pages. Footer Privacy and Terms links describe the current preview rather than presenting a finalized live-service policy.

Home includes the requested sticky navbar, hero CTA, three service cards, six benefits, interactive four-step journey, module dashboard preview, authorized-family-profile preview, doctor section, reminder switches, FAQ accordion, final CTA and professional footer. About includes the introduction, problem/solution, mission/vision, five-step journey, care areas, planned privacy model, transparent team placeholder, roadmap and CTA.

Services includes 12 features per module from the supplied brief, plus fictional dashboard previews. Dedicated detail routes: `/services/child-care`, `/services/womens-health`, `/services/adult-health`. Additional routes: `/for-doctors`, `/contact`, `/privacy`, `/terms`.

Interactive demos are in `src/components/Sections.tsx`; detailed feature lists and FAQ content are in `src/data/features.ts`. Dashboard tabs, optional women’s trackers, BP/glucose selection, family-profile selection, reminder switches and journey steps use temporary React state. They do not store patient data, calculate vaccination schedules, send reminders, make appointments, verify doctors or provide clinical recommendations. Account services and a verified backend are future implementation work.

Images are generated, project-local assets in `public/images/`; their subjects and generation brief are documented there. Fonts load from Google Fonts, with local fallbacks.

Browser checks against a running local website: `node app/scripts/check-layout.mjs`, `node app/scripts/check-sections.mjs` and `node app/scripts/check-auth.mjs` from the repository root. They use installed Google Chrome through Playwright and write ignored screenshots in `app/.preview/`.

The reference-inspired layout fills the available page width without outer side gutters. Desktop type sizes remain fixed rather than scaling with the viewport on large monitors. Responsive breakpoints cover smaller laptops, tablets and mobile. Physical monitor inches and browser zoom are controlled by the device/browser, not by the website.

GSAP animates the hero and care-card entrances. Three.js is loaded separately for subtle decorative rings, stops rendering offscreen/in background tabs, and disposes resources when removed. Reduced-motion settings disable both animations and the 3D decoration. Service descriptions are introductory content, not connected health records or clinical functionality.
