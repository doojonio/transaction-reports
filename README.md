# Transaction Reports

A FastAPI-based microservice for analyzing user transaction data with aggregated metrics and country-based reporting.

## Overview

This service provides RESTful API endpoints to query and analyze transaction data with support for:
- Time-based transaction metrics (total, average, min, max)
- Daily shift calculations (percentage changes day-over-day)
- Country-based aggregation and reporting
- Filtering by transaction status and type
- Redis caching for improved performance

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Cache**: Redis
- **Migrations**: Alembic
- **Package Manager**: uv
- **Testing**: pytest with async support
- **Data Processing**: pandas

## API Endpoints

### `GET /report`

Get aggregated transaction metrics with optional filters and daily breakdowns.

**Query Parameters:**
- `start_date` (date, optional): Start of date range (default: 30 days ago)
- `end_date` (date, optional): End of date range (default: today)
- `status` (string): Filter by transaction status (`SUCCESSFULL`, `FAILED`, or `all`)
- `type` (string): Filter by transaction type (`PAYMENT`, `INVOICE`, or `all`)
- `include_avg` (boolean): Include average metrics (default: `false`)
- `include_min` (boolean): Include minimum metrics (default: `false`)
- `include_max` (boolean): Include maximum metrics (default: `false`)
- `include_daily_shift` (boolean): Include day-by-day breakdown with percentage changes (default: `false`)

**Response:**
```json
{
  "total": "394917.35",
  "avg": "497.35",
  "min": "1.23",
  "max": "999.99",
  "items": [
    {
      "date": "2025-01-15",
      "total": "12345.67",
      "total_daily_shift": "5.2"
    }
  ]
}
```

### `GET /report/by-country`

Get transaction metrics aggregated by country.

**Query Parameters:**
- `sort_by` (string, optional): Sort field (`total`, `count`, or `avg`)
- `top_n` (integer, optional): Limit results to top N countries

**Response:**
```json
{
  "items": [
    {
      "country": "United States",
      "avg": "525.72",
      "total": "262859.27",
      "count": 500
    }
  ]
}
```

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "health": "ok"
}
```

## Quick Start with Docker

The easiest way to run the application is using Docker Compose:

```bash
# Start all services (PostgreSQL, Redis, FastAPI app)
docker compose up -d

# The application will automatically:
# - Run database migrations
# - Seed mock data (100 users with 100 transactions each)
# - Start on http://localhost:8000
```

**Access the application:**
- API Documentation: http://localhost:8000/docs
- API: http://localhost:8000
- Health Check: http://localhost:8000/health

**Stop services:**
```bash
docker compose down

# To also remove volumes (database data):
docker compose down -v
```

For detailed Docker setup, configuration, and troubleshooting, see **[DOCKER.md](DOCKER.md)**.

## Local Development

### Prerequisites

- Python 3.13+
- PostgreSQL 16+
- Redis 7+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis URLs
   ```

3. **Run database migrations:**
   ```bash
   uv run alembic upgrade head
   ```

4. **Start the application:**
   ```bash
   uv run uvicorn main:app --reload
   ```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov app --cov-report=term

# Run specific test file
uv run pytest tests/routes/test_report.py -v
```

## Project Structure

```
.
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── queries/         # Complex query builders
│   ├── routes/          # API endpoints
│   ├── schemas/         # Pydantic models
│   ├── services/        # Business logic
│   ├── policies/        # Configuration (cache TTL, etc.)
│   └── utils/           # Helper functions
├── tests/               # Test suite
├── alembic/             # Database migrations
├── shared/external/     # External data (user countries CSV)
├── docker-compose.yml   # Docker orchestration
├── Dockerfile           # Application container
└── main.py              # Application entry point
```

## CI/CD

GitHub Actions workflow automatically runs on push/PR:
- Sets up Docker Compose environment
- Runs database migrations
- Executes full test suite with coverage

See `.github/workflows/ci.yml` for details.

## License

See [LICENSE](LICENSE) file for details.
