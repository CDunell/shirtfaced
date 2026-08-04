# Oracle Cloud Deployment and Local Runbook

## Production assumptions

- The application runs in the user's existing Oracle Cloud environment.
- PostgreSQL already exists and is reachable from the application host.
- The application is deployed as one FastAPI service.
- Generated assets initially use a persistent mounted directory.
- Oracle Object Storage can be added later through the asset adapter.

## Required production information

Configure:

- PostgreSQL host
- PostgreSQL port
- database name
- application database user
- password or secret reference
- TLS mode
- application public or private hostname
- persistent asset directory
- reverse-proxy configuration
- backup policy

## PostgreSQL role

Create a dedicated least-privilege role for Shirtfaced Studio.

Example:

```sql
CREATE ROLE shirtfaced_app LOGIN PASSWORD 'replace-through-secret-management';
CREATE DATABASE shirtfaced_studio OWNER shirtfaced_app;
```

Where the database already exists, grant only the schema and object permissions required by Alembic and the application.

Do not use the PostgreSQL superuser as the runtime account.

## Environment

```env
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=
OPENAI_REVIEW_MODEL=
OPENAI_IMAGE_MODEL=
OPENAI_IMAGE_SIZE=1536x1024
OPENAI_IMAGE_QUALITY=high
OPENAI_TIMEOUT_SECONDS=180

DATABASE_URL=postgresql+psycopg://shirtfaced_app:password@postgres-host:5432/shirtfaced_studio
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT_SECONDS=30
DB_POOL_RECYCLE_SECONDS=1800
DB_SSLMODE=require

WORLDS_ROOT=/srv/shirtfaced/worlds
ASSETS_ROOT=/srv/shirtfaced/assets
ASSET_STORE=filesystem

GIT_ENABLED=true
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
```

Do not place production secrets in the repository.

Use Oracle Cloud Vault, an existing secret mechanism, or protected service environment variables.

## Local development

Prerequisites:

- Python 3.12+
- Git
- Docker or access to a development PostgreSQL database
- OpenAI API key for manual runs

Create the environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Start a local PostgreSQL container if required:

```bash
docker run --name shirtfaced-postgres \
  -e POSTGRES_USER=shirtfaced \
  -e POSTGRES_PASSWORD=shirtfaced \
  -e POSTGRES_DB=shirtfaced_studio \
  -p 5432:5432 \
  -d postgres:16
```

Apply migrations and run:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

## Production deployment shape

Recommended:

```text
Internet or private network
        |
Oracle Cloud load balancer or reverse proxy
        |
FastAPI application service
        |
Existing PostgreSQL
        |
Persistent asset volume
```

Run the application behind HTTPS.

Bind FastAPI to the internal interface and let the reverse proxy terminate TLS.

## Migration process

Production deployments must:

1. back up the database;
2. deploy application code;
3. run `alembic upgrade head` as a controlled release step;
4. start or restart the application;
5. verify `/health` and `/ready`;
6. run a smoke test;
7. retain rollback instructions.

Do not let every application worker run migrations on startup.

## PostgreSQL backups

Use the existing Oracle/PostgreSQL backup regime where available.

At minimum:

- daily database backup;
- retention appropriate to the brand's production value;
- periodic restore test;
- backup before migrations;
- separate backup of `WORLD.md`, `CONTINUITY.md`, `SHOTLIST.md` and approved assets.

## Connection and network security

- Restrict PostgreSQL ingress to the application host or private subnet.
- Require TLS where supported.
- Use a dedicated application role.
- Rotate credentials.
- Never expose PostgreSQL directly to the public internet.
- Configure statement and connection timeouts.
- Log failed connections without logging passwords.

## Asset persistence

Generated images must not live only inside an ephemeral container.

For filesystem storage:

- mount a persistent Oracle block volume;
- store images outside the application code directory;
- back up approved references;
- store paths relative to `ASSETS_ROOT`.

For future Oracle Object Storage:

- preserve the same `AssetStore` interface;
- use object keys instead of absolute paths;
- use signed URLs only when needed;
- keep the bucket private.

## Quality commands

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

Integration tests should use PostgreSQL.

## Git policy

Recommended branches:

- `main`
- `feat/<scope>`
- `fix/<scope>`

Do not commit:

- `.env`
- database dumps containing secrets
- generated working images unless intentionally preserving approved references
- temporary thumbnails
- API payload logs

## Recovery

### PostgreSQL available, Markdown missing

Restore Markdown from Git or the world backup.

### Markdown available, PostgreSQL missing

Restore PostgreSQL from backup. If impossible, run an explicit reconciliation import and require manual review.

### Review failed

Retry review against the existing image. Do not regenerate.

### Image generation failed

Retry only after showing the error. Record the failure.

### Asset volume unavailable

Mark the application not ready. Do not generate images until durable storage is restored.
