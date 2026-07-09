# Deployment (GitHub Actions → Hetzner)

Every push to `main` (or a manual workflow run) builds two images (`backend` and
`frontend`), publishes them to **GHCR**, and deploys them on the VPS over SSH
with `docker-compose.prod.yml`.

```
push main ─▶ build amd64 (backend + frontend) ─▶ push GHCR ─▶ scp compose+Caddyfile ─▶ ssh: pull + up -d
```

Relevant files:
- [.github/workflows/deploy.yml](../.github/workflows/deploy.yml) — the pipeline.
- [docker-compose.prod.yml](../docker-compose.prod.yml) — self-contained prod stack (GHCR images).
- [caddy/Caddyfile](../caddy/Caddyfile) — config for Strategos's INTERNAL Caddy (strategos-caddy, no host ports).
- `.env.deploy.example` — template for the server's interpolation `.env`.

> **Dev is unaffected.** `docker-compose.yml` (with `build:` and hot-reload) stays
> exactly the same: `docker compose up` locally works as before.

This stack shares a VPS with other projects (`craze-commercial-platform`,
`solar-lead-generator`, ...), each with its own internal Caddy hooked into the
external `proxy` network, all behind the entry Caddy managed in the
[`Koalvia/infra`](https://github.com/Koalvia/infra) repo (owns the host's 80/443).

---

## 1. GitHub secrets (Settings → Secrets and variables → Actions)

| Secret | What it is |
|---|---|
| `SERVER_IP` | Hetzner VPS IP |
| `SSH_USERNAME` | SSH user (`root`) |
| `SSH_PRIVATE_KEY` | SSH private key whose public half is in the VPS's `~/.ssh/authorized_keys` |
| `CR_PAT` | Personal Access Token (classic) with **`read:packages`** scope. Used by the VPS to `docker login ghcr.io` and pull the private images |

> The CI push to GHCR uses the automatic `GITHUB_TOKEN` (nothing to create there).
> `CR_PAT` is only so the **server** can *pull* the images. If you make the packages
> public instead (see 2.5), `CR_PAT` is no longer needed.

---

## 2. Preparing the VPS (one-time)

### 2.1 Docker
Already installed on this VPS (shared with other projects).

### 2.2 DNS
- Point an **A** record: `strategos-platform.koalvia.com` → VPS IP.
- Ports **80/443** are already owned by the existing entry Caddy (`Koalvia/infra`);
  Strategos does not touch them.

### 2.3 Create the directory and the `.env` files (secrets live here, not in GitHub!)
```bash
mkdir -p ~/strategos-platform/backend ~/strategos-platform/frontend
cd ~/strategos-platform
```

Create **three** `.env` files (the workflow fails if any are missing):

**`./.env`** — compose interpolation (see `.env.deploy.example`):
```dotenv
PROXY_NETWORK=proxy
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=strategos_db
```

**`./backend/.env`** — backend secrets. Start from `backend/.env.example` in the repo and fill in:
```dotenv
APP_ENV=production
SECRET_KEY=<random, min 32 chars>
CORS_ORIGINS=["https://strategos-platform.koalvia.com"]
FRONTEND_URL=https://strategos-platform.koalvia.com
RESEND_API_KEY=<real Resend key>
RESEND_FROM_EMAIL=noreply@koalvia.com
TESTING=0
```
> No need to set `DATABASE_URL` or `REDIS_URL`: the prod compose points them at
> the internal `db` and `redis` services.
>
> While `RESEND_API_KEY` isn't a real key, the verification email send fails
> silently (registration/login still work, but the user needs to be verified by
> hand — see "First deploy" below).

**`./frontend/.env`** — frontend config (server-side vars, read at runtime):
```dotenv
NEXT_PUBLIC_API_KEY=<the api_client key created in the backend, see "First deploy">
# NEXT_PUBLIC_API_URL is set by the compose to http://api:8000 (don't put it here)
```

> Permissions: `chmod 600 .env backend/.env frontend/.env`.

### 2.4 Entry Caddy: shared network + site block

Already resolved for this VPS (shared with craze/solar-lead-generator): the
`proxy` network already exists and the entry Caddy is already connected to it.
The site block for Strategos lives in
[`Koalvia/infra`](https://github.com/Koalvia/infra) (`caddy/Caddyfile`):

```caddy
strategos-platform.koalvia.com {
    reverse_proxy strategos-caddy:80
}
```

To apply changes to that file: edit it in the `Koalvia/infra` repo, `git push`,
then on the VPS:
```bash
cd ~/infra && git pull
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```
The entry Caddy automatically issues the TLS certificate for
`strategos-platform.koalvia.com` (requires DNS to already resolve) and forwards
plain HTTP to `strategos-caddy`, which in turn routes to the frontend (see
[caddy/Caddyfile](../caddy/Caddyfile), Strategos's internal config).

### 2.5 Private GHCR
Images are private by default. The VPS logs in with `CR_PAT` (done by the
workflow). If you prefer, mark the packages
(`strategos-platform-backend`/`-frontend`) as public on GitHub and the server
login becomes optional.

---

## 3. Deploying

- **Automatic:** `git push` to `main`.
- **Manual:** *Actions* tab → *Deploy* → *Run workflow*.

The first time, the `api` container runs the migrations (`RUN_MIGRATIONS=1`).

**First deploy — create the API key (empty DB):** `frontend/.env` needs a
`NEXT_PUBLIC_API_KEY` that exists in `api_clients`. A fresh DB has none yet:
```bash
cd ~/strategos-platform
docker compose -f docker-compose.prod.yml exec api python scripts/create_api_client.py --name frontend-app
# copy the key -> put it in frontend/.env (NEXT_PUBLIC_API_KEY=...) and recreate the frontend:
docker compose -f docker-compose.prod.yml up -d --force-recreate frontend
```

**First deploy — seed the Usuarios directory (optional):**
```bash
docker compose -f docker-compose.prod.yml exec api python -m scripts.seed_staff_users
```

**Verify a user by hand** (while `RESEND_API_KEY` isn't real and the
verification email doesn't arrive):
```bash
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d strategos_db \
  -c "UPDATE users SET is_verified = true WHERE email = '<email>';"
```

Check the deployment:
```bash
ssh hetzner-koalvia
cd ~/strategos-platform
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f caddy api frontend worker
# and that strategos-caddy and the entry Caddy share the proxy network:
docker network inspect proxy --format '{{range .Containers}}{{.Name}} {{end}}'
```

---

## 4. Rollback

Every build also leaves an immutable `sha-XXXXXXX` tag in GHCR. To roll back,
pin the tag in the server's `./.env` and relaunch:
```dotenv
BACKEND_IMAGE=ghcr.io/davidalonsobadia/strategos-platform-backend:sha-abc1234
FRONTEND_IMAGE=ghcr.io/davidalonsobadia/strategos-platform-frontend:sha-abc1234
```
```bash
docker compose -f docker-compose.prod.yml up -d
```
