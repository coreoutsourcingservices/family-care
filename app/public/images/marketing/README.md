# Home and About redesign

The local public routes `/` and `/about` use the mint/teal reference composition, existing FamilyCare+ branding, blue Child Care cards and responsive layouts. Other routes keep their existing layouts. Buttons use existing service, customer and doctor routes.

## Assets

Created using the built-in `image_gen.imagegen` tool, then converted to WebP for local delivery. Original generated PNG files remain in the Codex generated-images directory. No remote image host is required.

- `app/public/images/marketing/family-hero.webp` — family hero (176 KB).
- `app/public/images/marketing/about-family-hero.webp` — doctor/family hero (196 KB).
- `app/public/images/marketing/care-journey.webp` — transparent clinic illustration (130 KB).
- `app/public/images/marketing/care-portraits.webp` — four illustrative clinician portraits (136 KB).

Existing `/images/child.png`, `/images/women.png` and `/images/adult.png` are reused for service cards. Portraits are synthetic illustrations for care categories, not real provider identities. Company dates, ratings and patient testimonials are not invented. Public published health articles open in a readable dialog; when no articles are returned, service guide links appear instead.

## Image generation prompts

### Family hero

Create one production website hero background image, 1792 by 1024 landscape. Photorealistic premium healthcare lifestyle advertising with subtly polished 3D studio art direction. A joyful Indian multigenerational family of six: mother, father, two school-age children, grandmother in a warm light sari, grandfather with glasses and white beard. They lean together, smile and look upward with authentic natural faces, natural hands, warm ivory and peach clothing. Composition: the entire family is tightly grouped on the RIGHT 60 percent, cropped at waist at bottom; LEFT 40 percent is clean empty pale mint green negative space for website headline. Background seamless soft sage/mint gradient, luminous ivory-outline medical plus signs behind family, subtle organic studio shapes. Match sophisticated teal/mint family healthcare website reference. Soft warm daylight, extremely clean professional photography, high fidelity realistic skin. No text, letters, logos, UI, watermark, badges, borders, or additional people. Not a website screenshot, only hero photograph/background.

### About hero

Create one premium healthcare website About hero background photograph, 1792 by 1024 landscape. On the RIGHT 60 percent a compassionate Indian male doctor in his forties wearing white coat and stethoscope warmly shakes the hand of a smiling elderly Indian grandfather wearing beige knitwear and glasses; smiling grandmother and young adult Indian couple stand closely beside them. Natural anatomy, believable hands, high fidelity faces, respectful warm candid expressions. LEFT 40 percent entirely empty mint-green softly lit background reserved for webpage typography. Seamless mint/sage studio gradient, warm glowing rounded medical plus outlines in background, subtle sculptural pastel foliage at edges and stylized soft tree canopy in upper right. Premium photorealistic advertising with polished dimensional botanical set, warm daylight, professional art direction. Subjects framed from waist up and aligned to bottom. No text, logos, UI, watermark. Only background asset, not a screenshot.

### Journey illustration

Create a single polished isometric 3D illustration for a premium mint and teal family healthcare website About story section. A winding soft mint road connects a tiny ivory and teal medical clinic, small hospital with terracotta medical cross, location pin, heart health tile, smartphone, trees and miniature rounded bushes. Sculptural clay-like smooth matte materials with glossy teal accents, warm cream bases and restrained peach/coral details. Gentle perspective, cohesive clear silhouette, studio ambient occlusion and soft ground shadow. Centered object group with generous transparent padding on all sides. No words, letters, labels, numbers or watermark. Transparent background, isolated complete illustration, landscape 4:3 framing.

### Clinician portrait sheet

Create one square editorial portrait contact sheet for a family healthcare website. EXACTLY four equal square photographic portraits in a seamless 2 by 2 grid, no gutters. Top left: smiling Indian male doctor age 35, dark short hair, white coat, pale sage background. Top right: smiling Indian female pediatric doctor age 35 with tied hair, white coat, warm ivory background. Bottom left: experienced Indian male physician age 55 with glasses and salt pepper hair, white coat, pale mint background. Bottom right: confident Indian female physician age 40 with shoulder length dark hair, white coat, pale peach background. Every subject is an illustrative synthetic person, not a real named doctor. Head and shoulders, eye level, centered face within each quadrant, soft professional studio lighting, high quality realistic photography, pleasant natural expressions, normal anatomy. Faces must be fully inside their own quadrant, with equal scale and margin. No words, names, letters, logos, UI, borders, text or watermark. Intended as one cohesive local image asset cropped into four circular care-category illustrations.

## Verification

- `npm run build --workspace app`
- `node app/scripts/check-marketing-pages.mjs`
- `node app/scripts/check-growth-navigation.mjs`

Marketing browser checks cover Home/About at 360, 390, 768, 1366 and 1920 pixels; images; horizontal overflow; mobile menu; search focus and Escape; services dropdown; carousel; published article reading; Child Care blue palette; and visit routing. Screenshots are written to `app/.preview/marketing-*.png`.
