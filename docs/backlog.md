# Backlog

Features listed here are picked up automatically by the Planner agent.

**How to trigger planning:**
- **Single push**: add a new `##` section below and push to `main` — the Planner
  reads the diff, creates ordered GitHub issues for each new entry, and stops.
  It will not re-process entries that already have a matching issue.
- **Manual full-pass**: run the `Agent - Plan` workflow manually via the Actions UI
  and point it at this file to process all entries (with deduplication).
- **Ad-hoc idea**: open a GitHub issue with your idea, add the `plan` label — the
  Planner reads that issue and creates sub-issues from it.

After the Planner runs, review the created issues and add the `auto` label to each
one (in dependency order) to hand it off to the Implementer.

---

<!-- Add new features below. Use a ## heading per feature and describe the goal,
     the target user, and what "done" looks like. Be as specific or as vague as you
     like — the Planner will ask clarifying questions before creating issues if the
     idea is too ambiguous to decompose safely. If a feature has a design mockup,
     commit it under `design/refs/<slug>/` (see `design/refs/README.md`) and mention
     that path in the entry — the Planner will read it and link it into the task
     issue(s) it creates. -->

<!-- The entries below are one connected initiative: the first working version of
     the Strategos platform. They depend on each other in the order listed
     (Rebrand -> BC mock layer -> Customers -> Projects -> Obligations -> Tasks ->
     Users -> Dashboard). Planner: consider one combined epic covering all of them,
     in this order, rather than a separate epic per entry. -->

## Rebrand: TaskFlow → Strategos

This repo started from the generic "TaskFlow" template (a personal to-do list app).
None of that product identity applies to Strategos, an asesoría i gestoria (tax,
accounting, and labor consultancy) platform for Andorra. Remove every TaskFlow-
specific name, string, and image while preserving the underlying architecture
(domain layout, service/router split, JWT + API-key security, Docker/Celery/Alembic
setup) as the foundation for the real product.

Target user: internal dev team — this is infra/copy cleanup, not an end-user
feature.

What "done" looks like:
- Replace "TaskFlow" (and slug variants like `taskflow_db`, `craze_dashboard`) with
  "Strategos" across docs (`README.md`, `backend/README.md`, `frontend/README.md`,
  `backend/DOCKER_USAGE.md`), env examples, docker-compose files, `Caddyfile`,
  `init.sql`, the CI workflow, the Celery app name, email templates
  (`app/core/email.py`), and any UI copy/titles/metadata in the login/register pages
  and `app/layout.tsx`.
- The `tasks` and `lists` backend/frontend domains are TaskFlow's own product (a
  personal to-do app) — they are not "rebranded," they are replaced by Strategos'
  real domains (see the entries below). Only their architectural pattern (domain
  folder layout, service/router split) is worth preserving, not their business
  behavior.
- Remove template-authoring meta content that describes the TaskFlow template
  itself rather than the Strategos product (e.g.
  `docs/blog/three-ways-to-ship-with-ai-agents.md`) — delete rather than rewrite.
- Leave the generic placeholder image assets under `frontend/public/`
  (`placeholder-logo.*`, `placeholder-user.jpg`, etc.) as-is for now — they aren't
  TaskFlow-branded by content; real Strategos branding assets aren't ready yet.
- Non-goals: do not change the JWT/API-key authentication mechanics, the
  domain-layout convention, or the Alembic/Celery/Docker/CI setup — only names,
  copy, and dead product content change.

---

## Business Central mock integration layer

Strategos' real data (customers, projects, users, obligations, tasks) will
eventually live in Microsoft Business Central and be consumed by this platform
through BC's REST API — the platform itself will not be the system of record. That
connection isn't available yet (pending `client_id`/`client_secret` and some BC-side
field changes on the vendor's end), so build a swappable integration seam now: an
abstract client interface mirroring the agreed BC endpoints, with a mock
implementation returning realistic fixture data. Every feature below is built and
demoed against this stable contract now, and pointed at the real BC API later by
swapping one implementation — no callers change.

Target user: internal dev team; this unblocks every product-facing entry below.

Endpoints to mirror (confirmed with the BC integrator; shape only — no BC
credentials exist yet, so this returns mock data only in this round):
- `GET /customers`
- `GET /projects`
- `GET /users`
- `GET /userTasks`
- `GET /obligations`
- `GET /projectObligations`

What "done" looks like:
- An interface/port (e.g. `app/integrations/business_central/client.py`) with one
  method per endpoint above, returning typed Pydantic models.
- A `MockBusinessCentralClient` implementation backed by fixture data, realistic
  enough to drive the Dashboard/Clientes/Proyectos/Tareas/Usuarios/Obligaciones
  screens end to end — aim for parity with the names/numbers already shown in
  `design/refs/platform-mvp/dashboard-mock.html` (8 customers, ~12 projects, the
  named users, the obligation types from the "fitxa de projecte" structure
  described in the Projects and Obligations entries below).
- A config switch (e.g. `settings.BUSINESS_CENTRAL_MODE`, default `mock`) that
  selects the implementation via dependency injection, so a future
  `LiveBusinessCentralClient` can be dropped in behind the same interface without
  touching any service/router code.
- No Postgres tables, models, or Alembic migrations for BC-owned entities
  (customers, projects, obligations, project-obligations, BC-sourced task fields) —
  this data is never persisted locally, by design; see the architecture note below.
- Explicitly do not implement the real BC HTTP client, its OAuth flow, or reference
  any tenant/environment identifiers already shared informally by the integrator —
  those stay out of committed docs/code until real credentials exist. This task is
  mock-only.

Architecture note for the Implementer: domains that read BC data (customers,
projects, obligations, tasks) should have `schemas.py` + `service.py` (calling the
BC client) + `router.py`, but skip `models.py`/Alembic — there is nothing of ours to
persist. This is a deliberate deviation from the domain layout in `CLAUDE.md` §4
(which assumes a DB-backed domain); call it out in the PR description so the
Reviewer doesn't flag a "missing migration" as an oversight.

---

## Customers domain (Clientes)

Give the firm's staff a single searchable directory of their ~300–400 clients
(companies, individuals, estates, communities, foundations), replacing scattered
manual tracking.

Target user: any Strategos staff member (Soci Director, Responsable Fiscal/Laboral,
técnicos) looking up a client.

What "done" looks like:
- New `customers` domain (read-only in this round — Business Central remains the
  system of record; no create/update/delete from this platform yet) backed by the
  mock BC client's `/customers` data: name, NIF/CIF, entity type (Societat /
  Persona física / Indivís / Comunitat de béns / Fundació / Altres), responsible
  staff member, active project count, status (Activo/Inactivo).
- Frontend `Clientes` page: searchable/filterable table matching
  `design/refs/platform-mvp/dashboard-mock.html` (Clientes view) — search by
  name/NIF, filter by status, columns Cliente/NIF/Tipo/Responsable/Proyectos/Estado.

Design references: `design/refs/platform-mvp/clientes.png`,
`design/refs/platform-mvp/dashboard-mock.html`

Depends on: Business Central mock integration layer.

Non-goals: no create/edit/delete UI for customers in this round.

---

## Projects domain & the project "fitxa" structure (Proyectos)

This is the client's core pain point: obligations must be tracked per project, not
per client, because one client (e.g. a holding group) can have many companies/
projects each with its own tax/accounting checklist. Model the project record
("fitxa de projecte") with the fields the client has already specified, sourced
from the mock BC `/projects` endpoint.

Target user: managers and técnicos who need to see, per project, who's
responsible, what type of engagement it is, and its certificate/status details.

Confirmed project record structure (from the client's "Fitxes de projectes" spec —
use this to shape the mock fixture data and the schema, all sourced read-only from
BC):
- **General**: project name, responsible, técnico, entity type (Societat/Persona
  física/Indivís/Comunitat de béns/Fundació/Altres), project type (Iguala
  mensual/trimestral/anual/Altres), has-certificate (yes/no) + expiry date, filing
  date.
- The **Comptable / Fiscal / CASS / Altres / Informes** subsections (CCAA, IS,
  IRPF, IGI, IRNR, bonificació IIEA, bonificació ITP/IGI, treballador per compte
  propi, generació de factures, generació d'informes) are the project's *obligation
  checklist* — modeled by the Obligations entry below (`/obligations` catalog +
  `/projectObligations` per-project instances), not duplicated here; this entry
  owns the General section only.
- `projects` domain: `schemas.py` + `service.py` (calling the BC mock client) +
  `router.py`, list + detail endpoints. No local table (see the architecture note
  in the BC integration entry).
- Frontend `Proyectos` page: card grid per
  `design/refs/platform-mvp/dashboard-mock.html` (Proyectos view) — name, client,
  tags (project type / entity type), responsable/técnico, next obligation due date,
  status.

Design references: `design/refs/platform-mvp/proyectos.png`,
`design/refs/platform-mvp/dashboard-mock.html`

Depends on: Business Central mock integration layer.

---

## Obligations catalog & per-project deadline tracking (Obligaciones)

The platform's single most requested capability: a deadline calendar per project so
nothing gets missed, visible to both managers and assigned staff. This directly
replaces the client's current manual tracking across 300–400 projects.

Target user: managers (oversight across all projects) and técnicos (their own
assigned obligations).

What "done" looks like:
- `obligations` domain: catalog of obligation types sourced from mock BC
  `/obligations` (e.g. CCAA - dipòsit de comptes, IS, IRPF, IGI, IRNR, Bonificació
  IIEA, Bonificació ITP/IGI, Treballador per compte propi (CASS), Generació de
  factures, Generació d'informes), each with its periodicity
  (mensual/trimestral/semestral/anual) and due-date rule.
- Per-project obligation instances sourced from mock BC `/projectObligations`:
  which obligations apply to a given project (subjecte SI/NO), computed due date,
  submission date once filed, and a derived status (Vencido / Próximo / Al día)
  based on today's date vs. due date.
- Dashboard widgets: "Obligaciones próximas" KPI tile and the "Próximas
  obligaciones" list (obligation, project/client, status badge, due date) —
  aggregated across all projects.
- Dedicated `Obligaciones` page: same data as a full list/filter view (filter by
  status/project/date range).

Design references: `design/refs/platform-mvp/dashboard.png`,
`design/refs/platform-mvp/dashboard-mock.html` (Dashboard KPI tiles + "Próximas
obligaciones" widget — there is no dedicated Obligaciones-page screenshot; the nav
item exists but wasn't captured, so extrapolate the full list/filter view from this
widget)

Depends on: Business Central mock integration layer, Projects domain (for
project/client display names).

---

## Internal tasks (Tareas), sourced from Business Central's userTasks

The day-to-day task board staff use (Pendiente/En curso/Hecho), tied to a project
instead of the old TaskFlow "list" concept.

Target user: técnicos and managers tracking their own and their team's day-to-day
work items.

What "done" looks like:
- Primary task data (title, project, assignee, due date, priority, status) is
  sourced from the mock BC `/userTasks` endpoint via the Business Central client —
  no local table for these fields.
- One small local table for anything genuinely not covered by BC (e.g. internal
  comments/notes, or fully platform-native ad hoc tasks with no BC counterpart),
  with its own Alembic migration. Keep it minimal for this round: only add fields
  actually needed to make the Tareas board and dashboard widget work; do not
  speculatively model fields BC might one day provide.
- Retire the existing `lists` domain and the `list_id`/`recurrence`/
  `parent_task_id` TaskFlow-era fields on `tasks` entirely — they belonged to the
  old personal to-do app and have no Strategos equivalent (a project is not a
  list).
- Frontend `Tareas` page: kanban board (Pendiente / En curso / Hecho columns) per
  `design/refs/platform-mvp/dashboard-mock.html`, task cards showing title,
  project, priority badge, due date, assignee avatar.
- Dashboard "Mis tareas de hoy" widget: the logged-in user's own tasks due
  today/soon.

Design references: `design/refs/platform-mvp/tareas.png`,
`design/refs/platform-mvp/dashboard-mock.html`

Depends on: Business Central mock integration layer, Projects domain.

---

## Users directory & roles (kept on our side)

Business Central identity/MFA integration isn't available yet, so authentication
and user management stay exactly as they are today (local JWT auth + hashed
passwords, from the existing `auth` domain) rather than moving to BC/Microsoft
identity. This entry only adds the role information the UI needs to show "who's
who."

Target user: all staff (login) and managers (staff directory).

What "done" looks like:
- Extend the existing local `auth.User` model with a `role` field (covering at
  least: Soci Director, Responsable Fiscal, Responsable Laboral, Tècnic Comptable,
  Tècnica Administrativa, Administració) — one Alembic migration.
- Seed/update local users to reflect the actual Strategos staff shown in the
  mockup (names/roles only — real emails/credentials are provisioned separately,
  never hardcoded).
- Frontend `Usuarios` page: staff table (Nombre/Rol/Email/Tareas activas) per
  `design/refs/platform-mvp/dashboard-mock.html`.
- Explicitly out of scope: consuming Business Central's `/users` endpoint for
  identity — that endpoint exists in BC per the integrator but is not used for
  login/authorization in this round; login stays 100% local. Revisit only once BC
  MFA/identity is actually wired up.

Design references: `design/refs/platform-mvp/usuarios.png`,
`design/refs/platform-mvp/dashboard-mock.html`

Non-goals: no change to the JWT/password/API-key mechanics themselves — keep
`app/domains/auth` and `app/domains/api_clients` as they are, just add the role
field.

---

## Dashboard overview

The landing screen after login — an at-a-glance summary of what needs attention
today, tying every domain above together.

Target user: every logged-in user (content scoped to what's relevant to their
role — managers see firm-wide KPIs, técnicos see their own tasks).

What "done" looks like: per `design/refs/platform-mvp/dashboard-mock.html`
(Dashboard view) — greeting header, four KPI tiles (Proyectos activos, Obligaciones
próximas, Tareas pendientes, Clientes activos), "Próximas obligaciones" list, "Mis
tareas de hoy" list.

Design references: `design/refs/platform-mvp/dashboard.png`,
`design/refs/platform-mvp/dashboard-mock.html`

Depends on: Customers, Projects, Obligations, and Tasks entries above (build this
one last — it only composes their data).

---

## Not in this round (explicitly deferred — do not plan yet)

Captured from the client's requirements meeting for future backlog rounds. Listed
here only so nothing is lost — do not create issues for these yet:
- BOPA (Andorran Official Gazette) weekly monitoring agent matching publications
  against clients/projects.
- Automated monthly financial reporting (P&L, balance sheet, cash flow, deviation
  analysis) sent via email.
- Payroll automation (deferred by the client to Q4 2026).
- Other AI agents discussed (invoice-vs-contract checker, bank reconciliation,
  contract compliance checks, digital certificate expiry alerts, automatic
  billing/collections).
- The real (non-mock) Business Central API client — blocked on
  `client_id`/`client_secret` and BC-side schema changes; do not start until those
  exist.
