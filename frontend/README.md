# Display Check frontend

Initial presentation foundation on `develop-v2`: Next.js App Router, React,
TypeScript, and plain CSS. No backend behavior or contracts are changed.

## Local development

Use Node.js 20.9+ (Node 24 LTS recommended) and the existing Python environment.
From the repository root, start the authoritative API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Visit http://localhost:3000 and http://localhost:3000/project.

`DISPLAY_CHECK_API_URL` is the API origin (default `http://127.0.0.1:8000`),
without `/api`. It is read only on the Next.js server. Restart Next.js after
changing it. No public environment variable, browser API fetch, CORS change,
proxy route, or secret exposure is needed.

Home reads `/api/displays` and `/api/health` server-side, without caching and
with a three-second timeout. Independent Suspense boundaries let the page shell
render while reads complete. The development-only health indicator appears at
the bottom of Home; production still checks connectivity without displaying it.
An offline API yields a neutral family-list message; there is no fallback data.
Reload Home after restoring the API. API types mirror the existing response
contracts and do not implement domain validation or business rules.

## Structure

- `app/`: root layout, Home, workspace route, semantic design tokens and CSS.
- `components/`: header, imagery placeholder, registry list, health status,
  workspace shell, disabled controls, canonical stage, and output empty states.
- `lib/api.ts`: server-only typed helper limited to the two GET endpoints.

All components currently render on the server. Future browser interaction can
be introduced through small client components. Route pages remain separate
from the shared layout so authentication can be introduced later.

Fraunces and Archivo are self-hosted through Fontsource packages, imported once
in the layout and referenced through CSS typography tokens. No font service is
contacted at build or runtime. Temporary colors, spacing, radii, shadows, and
transitions are centralized in `app/globals.css` for later KKG branding.
`DisplayImagery` is a replaceable abstract paper composition, not a display
model. The canonical stage contains no display geometry or dimensions.

## Verification

```powershell
npm run build
npm run lint
npm run typecheck
```

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/v2 tests/api -q
git diff --check
git status --short
```

With both servers running, confirm both routes return HTTP 200, the Home list
matches `/api/displays`, and Home shows `Development API · Connected`. With
the API stopped, confirm the unavailable state appears and the workspace still
renders. Check keyboard focus and narrow layouts in a browser.

Intentionally deferred: authentication/Clerk, persistence, project analysis,
estimate submission, pricing, active configuration, visual generation,
reference uploads, canonical assets, carousel behavior, and deployment setup.

## Foundation verification results

- Installed with portable Node 24.21.0 / npm 11.19.0; lockfile resolves
  Next.js 16.3.5. npm audit reported zero vulnerabilities.
- Production build, ESLint, and TypeScript checks passed.
- Headless Edge: both routes returned HTTP 200; Home's family labels matched
  the real API; development health showed Connected; the CTA opened `/project`.
- Skip-link keyboard focus and disabled input/select controls passed.
- Neither route overflowed horizontally at 320, 390, or 768 pixels;
  desktop screenshots were visually reviewed. No browser page errors occurred.
- With the API stopped, both routes still returned HTTP 200 and Home showed
  the unavailable state.
- Existing Python tests: 199 passed. One existing Starlette/httpx deprecation
  warning was emitted.
- `git diff --check` passed; changes are confined to the new `frontend/` tree.

Install warnings: ESLint 9.39.5 is marked unsupported by its publisher;
the Next.js-compatible lint configuration passed. npm also reported an
unapproved `unrs-resolver` postinstall script; no approval was needed for
the successful build and lint checks. Revisit tooling versions in a later
maintenance pass. Next.js generated `AGENTS.md` and `CLAUDE.md` on first dev
startup; these are included as framework guidance.
