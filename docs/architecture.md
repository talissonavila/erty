# ERTY Backend Architecture

## Layers

### API

Receives HTTP requests, validates input, and returns HTTP responses.
Business rules must not be implemented here.

### Services

Contains the application's business rules and orchestrates repositories.

### Repositories

Responsible for persistence and database access.

### Database

Provides the SQLAlchemy engine, sessions, and migrations.

### Schemas

Defines request and response models using Pydantic.
Schemas are responsible for data validation and API contracts.

## Directory structure

```
erty
├─ adr
├─ backend
│  ├─ alembic
│  │  └─ __init__.py
│  ├─ app
│  │  ├─ api
│  │  │  └─ __init__.py
│  │  ├─ core
│  │  │  └─ __init__.py
│  │  ├─ db
│  │  │  └─ __init__.py
│  │  ├─ models
│  │  │  └─ __init__.py
│  │  ├─ repositories
│  │  │  └─ __init__.py
│  │  ├─ schemas
│  │  │  └─ __init__.py
│  │  ├─ services
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ Dockerfile
│  ├─ pyproject.toml
│  ├─ README.md
│  ├─ tests
│  │  ├─ api
│  │  │  └─ __init__.py
│  │  ├─ integration
│  │  │  └─ __init__.py
│  │  ├─ unit
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ CHANGELOG.MD
├─ CONTRIBUTING.md
├─ docker-compose.yml
├─ docs
│  └─ architecture.md
├─ PROJECT_CONTEXT.md
├─ README.md
└─ ROADMAP.md

```
## Dependency direction

API → Services → Repositories → DB