# Docker Setup Guide

This guide explains how to run the Transaction Reports application using Docker.

## Quick Start

To start the entire application stack (PostgreSQL, Redis, and the FastAPI app) with mock data:

```bash
docker-compose up -d
```

This will:
1. Start PostgreSQL database on port 5432
2. Start Redis cache on port 6379
3. Build and start the FastAPI application on port 8000
4. Run database migrations automatically
5. Seed the database with mock transaction data

## Accessing the Application

Once the containers are running:

- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
  - User: `transaction-reports`
  - Password: `s3cret_pw0123`
  - Database: `transaction-reports`
- **Redis**: localhost:6379

## Available Commands

### Start the stack
```bash
docker-compose up -d
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Stop the stack
```bash
docker-compose down
```

### Stop and remove volumes (clean slate)
```bash
docker-compose down -v
```

### Rebuild the application
```bash
docker-compose up -d --build
```

### Execute commands in the app container
```bash
# Run tests
docker-compose exec app uv run pytest

# Access Python shell
docker-compose exec app uv run python

# Run alembic migrations
docker-compose exec app uv run alembic upgrade head
```

### Access PostgreSQL
```bash
docker-compose exec postgres psql -U transaction-reports
```

### Access Redis CLI
```bash
docker-compose exec redis redis-cli
```

## Environment Variables

The application uses the following environment variables (configured in docker-compose.yml):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `MOCKFILL`: Set to `true` to automatically seed the database with mock data on startup

## Architecture

The Docker setup consists of three services:

1. **postgres**: PostgreSQL 16 database with persistent volume
2. **redis**: Redis 7 cache (Alpine Linux)
3. **app**: FastAPI application built from the Dockerfile

The application service:
- Waits for PostgreSQL and Redis to be healthy before starting
- Runs database migrations automatically via the entrypoint script
- Seeds the database with mock data if `MOCKFILL=true`
- Exposes the API on port 8000

## Troubleshooting

### Port conflicts
If ports 5432, 6379, or 8000 are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"  # Use 5433 on host instead of 5432
```

### Database connection issues
Check that PostgreSQL is healthy:
```bash
docker-compose ps
docker-compose logs postgres
```

### Application not starting
Check the application logs:
```bash
docker-compose logs app
```

### Reset everything
To completely reset the environment:
```bash
docker-compose down -v
docker-compose up -d --build
```

## Development Workflow

For local development with hot-reload:

1. Stop the app container:
   ```bash
   docker-compose stop app
   ```

2. Run the app locally:
   ```bash
   source .venv/bin/activate
   uvicorn main:app --reload
   ```

3. Keep PostgreSQL and Redis running in Docker:
   ```bash
   docker-compose up -d postgres redis
   ```

## Production Considerations

For production deployment, consider:

1. Using environment-specific configuration files
2. Enabling HTTPS/TLS
3. Using Docker secrets for sensitive data
4. Setting up proper logging and monitoring
5. Configuring resource limits
6. Using a production-grade ASGI server configuration
7. Setting `MOCKFILL=false` to prevent data seeding
