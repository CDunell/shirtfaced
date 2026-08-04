# Oracle Cloud Production Specification

## Assumption

Shirtfaced Studio will be deployed into an existing Oracle Cloud environment with access to an existing PostgreSQL service.

This document intentionally avoids assuming whether PostgreSQL is:

- Oracle Database for PostgreSQL;
- PostgreSQL installed on an Oracle Compute instance;
- a containerised PostgreSQL service;
- another managed PostgreSQL endpoint reachable from Oracle Cloud.

The application uses a standard PostgreSQL connection string and does not depend on provider-specific database features beyond networking and secret handling.

## Application deployment

Deploy one application service.

Suitable targets include:

- Oracle Compute VM with systemd;
- Docker on an Oracle Compute VM;
- an existing container runtime.

Version 1 does not require Kubernetes.

## Recommended service layout

```text
/srv/shirtfaced/
├── app/
├── worlds/
├── assets/
└── backups/
```

Run under a dedicated operating-system account.

## Reverse proxy

Use the existing reverse proxy or install one such as Nginx or Caddy.

Responsibilities:

- HTTPS;
- request size limits;
- request timeout suitable for image generation;
- internal forwarding to FastAPI;
- access logs;
- optional IP restriction or authentication.

## PostgreSQL requirements

Minimum supported PostgreSQL version: 15.

Required capabilities:

- UUID
- JSONB
- partial indexes
- advisory locks
- `timestamptz`
- transactional DDL through Alembic where supported

## Connection strategy

Use a small SQLAlchemy pool because the application is low-volume.

Initial recommendation:

- pool size: 5
- max overflow: 10
- pool timeout: 30 seconds
- pool recycle: 1800 seconds
- pre-ping: enabled

Adjust only from observed usage.

If an external pooler such as PgBouncer already exists, document its transaction mode and ensure advisory-lock behaviour remains correct.

## Availability behaviour

The `/ready` endpoint fails when:

- PostgreSQL is unreachable;
- required migrations are missing;
- world files are unreadable;
- asset storage is not writable.

The `/health` endpoint only confirms that the process is alive.

## Secrets

Preferred order:

1. existing Oracle Cloud Vault integration;
2. protected service environment file readable only by the application account;
3. container secret mechanism.

Never embed secrets in source, Docker images, shell history or Markdown files.

## Backups

Back up three state classes:

1. PostgreSQL database;
2. world Markdown files and Git history;
3. approved image assets.

A database-only backup is incomplete.

## Monitoring

At minimum capture:

- application errors;
- OpenAI request IDs;
- generation duration;
- review duration;
- PostgreSQL connection failures;
- migration version;
- asset write failures;
- estimated API spend.

Do not log API keys, passwords or image base64 payloads.

## Deployment acceptance

Production deployment is accepted when:

1. Alembic migrations apply;
2. application connects using the dedicated PostgreSQL role;
3. `/health` succeeds;
4. `/ready` succeeds;
5. World 1 loads;
6. one fake-adapter workflow succeeds;
7. one controlled live generation succeeds;
8. approval survives restart;
9. Markdown and PostgreSQL state agree;
10. database and asset backup procedures are documented.
