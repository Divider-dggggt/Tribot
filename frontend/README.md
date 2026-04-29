# Frontend Testing

This guide uses Docker as the primary way to run frontend tests for consistent environments.

## Test Structure

- `test/components/` and `test/pages/` - Vitest + React Testing Library tests
- `test/e2e/` - Playwright end-to-end tests
- `test/setup.ts` and `test/test-utils.tsx` - shared setup and helpers

## Docker Testing

Run in this order:

1) Start services:

```
docker compose up
```

2) Install Playwright browser binaries in the frontend container (first time only):

```
docker compose exec frontend yarn playwright install --with-deps chromium
```

3) Run unit/component tests:

```
docker compose exec frontend yarn test:run:docker
```

4) Run coverage:

```
docker compose exec frontend yarn test:coverage:docker
```

5) Run e2e:

```
docker compose exec frontend yarn test:e2e:docker
```

## Coverage Report

After `test:coverage:docker`, coverage outputs are generated in:

- `frontend/coverage/`
- `frontend/coverage/lcov-report/index.html`

Open the coverage report in your browser:

```
# macOS
open frontend/coverage/lcov-report/index.html

# Linux
xdg-open frontend/coverage/lcov-report/index.html

# Windows (PowerShell / CMD)
start frontend/coverage/lcov-report/index.html
```

### Frontend Test Coverage
![Frontend Test Coverage](../images/front-end-test-coverage.png)