# Project Guide: FastAPI + LangChain (uv)

## Tech Stack
* **Package Manager:** `uv`
* **Python Version:** Python 3.12–3.13 (>=3.12, <3.14)
* **API Framework:** FastAPI
* **Orchestration:** LangChain
* **Testing:** Pytest
* **Frontend:** React
* **Containerization:** Docker Compose (ensure all services are defined here)

## Core Commands
* **Install dependencies:** `uv sync`
* **Add package:** `uv add <package>`
* **Run Dev Server:** `uv run fastapi dev main.py`
* **Run Tests:** `uv run pytest`
* **Linting:** `uv run ruff check . --fix`
* **Docker:** `docker-compose up --build`

## Coding Standards
* **Structure:** Follow a modular FastAPI structure (`app/api/`, `app/services/`, `app/models/`). Every file must be placed in the correct logical directory based on its responsibility.
* **LangChain:** Use LCEL (LangChain Expression Language) for chains. Always use `pydantic v2` for schemas.
* **Local Models:** If using Ollama or LocalAI, ensure they are referenced via service names in `docker-compose.yml`.
* **Async:** Use `async def` for FastAPI endpoints and LangChain `ainvoke`/`astream` methods.
* **Dependency Injection:** Use FastAPI's `Depends()` for all dependency injection in endpoints. Never manually pass dependencies as function arguments or create instances inline. Example: `async def my_endpoint(service: MyService = Depends(get_service))` instead of `async def my_endpoint(service: MyService)` with manual instantiation.
* **Tests:** Mirror the source directory hierarchy under `tests/` (e.g., `app/services/rag.py` → `tests/services/test_rag.py`). Keep unit tests co-located with the module they test whenever possible.

## Type Safety Standards
* **No Warnings:** All code must be free of type warnings. Code should pass static type checking without errors.
* **Full Type Annotations:** All functions must have complete type annotations:
  - Function parameters must have type hints
  - Function return types must be explicitly specified (e.g., `-> str`, `-> None`, `-> dict[str, Any]`)
  - Class methods and `__init__` must have return type annotations
  - Use `dict[str, Any]` instead of bare `dict` for better type clarity
* **Import Typing Utilities:** Use `from typing import Any, Optional, Union, etc.` when needed for complex types
* **Avoid `object` and `list` Without Type Parameters:** Use `list[T]` instead of `list`, `dict[K, V]` instead of `dict`
* **Proper Use of Union Types:** Use `X | None` (Python 3.10+) or `Optional[X]` for nullable types

## Class Design Principles
* **Single Responsibility:** Each class must have one well-defined purpose. Do not mix API logic with business logic.
* **Method Visibility:**
  - Public: `def method_name(self)` — part of the class API
  - Private: `def _method_name(self)` — internal implementation details
  - Static: `@staticmethod def method_name()` — when no instance state is needed
  - Class methods: `@classmethod def method_name(cls)` — for factory patterns
* **Abstract Base Classes:** Use `ABC` + `@abstractmethod` when defining service interfaces or contracts that implementations must follow.
* **Class Organization:** Order methods consistently:
  1. `__init__`
  2. `@property` / `@abstractmethod`
  3. Public methods
  4. Private methods (`_prefixed`)
  5. Special methods (`__str__`, `__repr__`)
* **Dependency Injection:** Pass dependencies through `__init__` rather than importing globally within methods.

## Mandatory Post-Task Workflow
After completing **any** code modification or new feature, you **MUST** execute these steps in order:
1. **Linting:** Run `uv run ruff check . --fix`.
2. **Unit Tests:** Run `uv run pytest` after **every** code change — no exceptions.
3. **Validation:** If tests fail, fix the code immediately and re-run until all tests pass.
4. **Docker Sync:** If new environment variables or dependencies were added, update the `Dockerfile` and `docker-compose.yml` accordingly.