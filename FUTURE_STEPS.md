# Future Steps

Ideas and strategic directions to explore after core functionality is stable and validated.

## Referral & partnership strategy

If the core product works well (program discovery, PI matching, application tracking, draft generation), a natural expansion is to position it as a **referral and onboarding bridge** into modern productivity tools — especially for institutional and legacy-industry users who still default to Google Workspace and Microsoft 365.

### Vision

- Become a high-trust entry point that helps users graduate from spreadsheets, email threads, and ad-hoc docs into structured workflows in tools like **Notion**, Airtable, Coda, and other alternatives.
- Target audiences in **higher education, clinical psychology, research labs, and other institutional settings** where change is slow but high-value when it happens.
- Use the product’s existing workflows (program tracking, research notes, PI outreach, application materials) as the **on-ramp** into sponsored partner tools.

### Why this could work

- Institutional users already trust the product for a specific, high-stakes workflow (grad school / research applications).
- Referral moments are natural: “export your tracker,” “sync your program list,” “organize PI research,” “template your statement drafts.”
- Legacy industries are more likely to adopt new software when it is introduced through a **domain-specific tool they already rely on**, not through a generic productivity pitch.
- Strong referral UX can influence **partnership deals, sponsorships, co-marketing, and revenue-share arrangements**.

### Product direction: make the referral tool really good

Build referral features as a first-class product surface, not an afterthought:

- **Contextual referrals** — suggest Notion (or alternatives) at the moment users need them: tracker export, research hub, deadline calendar, draft versioning.
- **One-click setup** — pre-built templates (program tracker, PI CRM, application timeline, research reading list) that map directly to data already in the app.
- **Institution-friendly positioning** — emphasize privacy, export portability, and compatibility with existing university workflows.
- **Measurable conversion** — track which referral paths work (tracker export vs. draft export vs. PI research bundle).
- **Partner-quality experience** — fast, reliable, polished onboarding so referred users actually stick with the destination tool.

### Partnership & sponsorship angle

- Pursue **Notion and similar companies as providing sponsors/providers** once referral volume and conversion are demonstrable.
- Pitch structure:
  - Domain-specific distribution (clinical psych / research applicants)
  - Qualified users with immediate setup intent (not cold signups)
  - Co-branded templates and onboarding flows
  - Potential for education/research program sponsorships
- Partnership outcomes to target:
  - Sponsored templates or workspace credits for users
  - Co-marketing (blog posts, grad-school guides, lab workflow content)
  - Revenue share or referral fees
  - Official “recommended workflow” status inside partner ecosystems

### Prerequisites before pursuing this

1. Core flows are reliable end-to-end (accreditation data, program discovery, PI discovery, tracker, drafts).
2. Users repeatedly complete meaningful workflows (not just one-time visits).
3. Referral integration is tested with real export/sync paths and clear user value.
4. Basic metrics exist: referral clicks, template installs, retained usage in partner tools.

### Open questions

- Which partner tool fits best first (Notion vs. Airtable vs. Coda) per workflow?
- What referral mechanics do partners support today (affiliate, app partnerships, template galleries)?
- What data can be shared vs. must stay local for institutional trust?
- Is the primary monetization path sponsorship, referral fees, or premium integrations?

## Deployment

See **[DEPLOY.md](DEPLOY.md)** for step-by-step instructions to deploy:

- **Backend** → Render free tier (`render.yaml` Blueprint)
- **Frontend** → GitHub Pages (`.github/workflows/deploy-pages.yml`)

General GitHub Pages notes: [GITHUB_PAGES_DEPLOYMENT.md](GITHUB_PAGES_DEPLOYMENT.md)
