# django-api-base (v2025)

Modern Django API base project with the latest Python, Django, and packages.

## Tech Stack

### Core Framework
- **Python**: 3.10 - 3.12 (< 3.13)
- **Django**: 5.2.x
- **Django REST Framework**: 3.16.x

### GraphQL
- **Graphene**: 3.4.x
- **Graphene-Django**: 3.2.x
- **GQL**: 4.0.x

### Channels & WebSocket
- **Django Channels**: 4.3.x
- **Channels Redis**: 4.3.x
- **Daphne**: 4.2.x
- **Django Channels GraphQL WS**: 1.0.0rc7 (Python 3.12 compatible)

### Development Tools
- **Package Manager**: uv (migrated from Poetry)
- **Linter/Formatter**: Ruff
- **Testing**: pytest 8.x

## Installation

### Prerequisites
- Python 3.10 or higher (< 3.13)
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd django-api-base-2025
```

2. Install dependencies:
```bash
uv sync --dev
```

3. Run tests:
```bash
uv run pytest
```

## Development

### Linting and Formatting

Run linter with auto-fix:
```bash
uv run ruff check . --fix
```

Format code:
```bash
uv run ruff format .
```

### Testing

Run all tests:
```bash
uv run pytest
```

Run specific test file:
```bash
uv run pytest tests/test_apibase.py -v
```

## Migration from Poetry to uv

This project has been migrated from Poetry to uv for faster dependency resolution and installation.

### Key Changes
- `poetry.lock` → `uv.lock`
- `[tool.poetry]` → `[project]` in pyproject.toml
- Git dependencies specified in `[tool.uv.sources]`
- Development dependencies in `[project.optional-dependencies]`

## Configuration

### Ruff Settings
The project uses Ruff for both linting and formatting with the following configuration:
- Line length: 119
- Import sorting: enabled (Django-aware)
- Python upgrades: enabled
- See `[tool.ruff]` section in `pyproject.toml` for details

## License

[License information here]

## Contributing

[Contributing guidelines here]
