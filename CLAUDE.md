# CLAUDE.md

## Overview

QA Testing API - a sandbox REST API for manual QA testing practice. FastAPI + PostgreSQL, Dockerized.

## Quick Reference

```
Production:  http://195.201.19.37:8001
Swagger:     http://195.201.19.37:8001/docs
Database:    postgresql://qa_user:qa_password@195.201.19.37:5433/qa_db
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL 16
- **Auth**: JWT (python-jose), bcrypt
- **Deployment**: Docker Compose on Coolify server

## Project Structure

```
qa-api/
├── src/
│   ├── main.py          # FastAPI app, lifespan, routes
│   ├── config.py        # Settings from env vars
│   ├── database.py      # SQLAlchemy engine, session
│   ├── models.py        # User, Category, Product, Order
│   ├── schemas.py       # Pydantic request/response models
│   ├── auth.py          # JWT creation, verification, role deps
│   ├── seed.py          # Test data generator
│   └── routers/         # API endpoints by domain
│       ├── auth.py      # /auth/login, /auth/register, /auth/me
│       ├── users.py     # /users CRUD
│       ├── categories.py
│       ├── products.py
│       ├── orders.py
│       └── admin.py     # /admin/reset, /admin/stats
├── Dockerfile
├── docker-compose.yaml
└── pyproject.toml
```

## Domain Model

| Entity | Key Fields | Relationships |
|--------|------------|---------------|
| User | email, username, role, is_active | has many Orders |
| Category | name, description | has many Products |
| Product | name, price, stock, sku, category_id | belongs to Category |
| Order | order_number, status, total_amount, user_id | belongs to User, many-to-many Products |

## Roles & Permissions

| Role | Users | Categories | Products | Orders | Admin |
|------|-------|------------|----------|--------|-------|
| admin | CRUD | CRUD | CRUD | CRUD (all) | Yes |
| tester | Read | CRUD | CRUD | CRUD (all) | No |
| viewer | Read | Read | Read | Read (own) | No |

## Test Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| tester | tester123 | tester |
| viewer | viewer123 | viewer |

## Key Commands

```bash
# Local dev
docker compose up --build

# Deploy (on server)
cd /data/qa-api && git pull && docker compose up -d --build

# Reset database to seed state
curl -X POST http://195.201.19.37:8001/admin/reset \
  -H "Authorization: Bearer <admin_token>"

# DB queries
psql "postgresql://qa_user:qa_password@195.201.19.37:5433/qa_db"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://qa_user:qa_password@db:5432/qa_db | DB connection |
| SECRET_KEY | qa-testing-static-secret-key-2024 | JWT signing key |
| APP_NAME | QA Testing API | Shown in Swagger |

## Deployment Setup

This API runs directly on the Coolify server (not via Coolify UI) for simplicity.

**Initial setup was:**
```bash
# 1. Created project locally
mkdir ~/repos/qa-api && cd ~/repos/qa-api
# ... wrote FastAPI app, Dockerfile, docker-compose.yaml

# 2. Pushed to GitHub
git init && git add . && git commit -m "Initial setup"
gh repo create qa-api --public --source=. --push

# 3. Cloned on server and started
ssh root@195.201.19.37
mkdir -p /data/qa-api && cd /data/qa-api
git clone https://github.com/igorslobodyanyuk/qa-api.git .
docker compose up -d --build
```

**To deploy updates:**
```bash
# Local: commit and push
cd ~/repos/qa-api
git add -A && git commit -m "Your change" && git push

# Server: pull and rebuild
ssh root@195.201.19.37 "cd /data/qa-api && git pull && docker compose up -d --build"
```

**One-liner from local:**
```bash
git push && ssh root@195.201.19.37 "cd /data/qa-api && git pull && docker compose up -d --build"
```

## Notes

- JWT `sub` claim must be string (RFC 7519) - user ID is stringified
- Swagger auth: paste token without "Bearer " prefix
- `/admin/reset` clears all data and reseeds (admin only)
- Orders use many-to-many with products via `order_items` table
- Server location: `/data/qa-api` on 195.201.19.37
