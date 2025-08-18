# Test Database Configuration

## Current Setup

### Local Development Tests
- **Database**: PostgreSQL (same as production)
- **Location**: Uses existing PostgreSQL instance from `.env` file
- **Storage**: Temporary test database created and destroyed per test run
- **Speed**: ~45 seconds for 31 tests

### CI/CD Tests (GitHub Actions)
- **Database**: SQLite in-memory (`:memory:`)
- **Location**: RAM - no disk storage
- **Storage**: Completely in-memory, destroyed after tests
- **Speed**: Expected ~15-20 seconds for 31 tests

## Database Locations

### Local PostgreSQL Test DB
```
Host: From PGHOST in .env
Database: test_<PGDATABASE>
User: From PGUSER in .env
```
**Note**: Test database is automatically created with `test_` prefix and destroyed after tests.

### CI SQLite Test DB
```
Location: :memory: (RAM only)
File: None - completely in-memory
```

## Test Optimization Features

### Speed Optimizations
- ✅ **FastTestCase**: Shared test data created once per test class
- ✅ **Disabled Migrations**: Uses `MIGRATION_MODULES = None` for speed
- ✅ **Dummy Cache**: No Redis dependency in tests
- ✅ **Dummy Email**: No external email service calls
- ✅ **MD5 Password Hasher**: Faster than bcrypt for tests

### CI/CD Optimizations
- ✅ **In-Memory Database**: SQLite `:memory:` for maximum speed
- ✅ **No External Services**: Mocked Cloudinary, Brevo, Paystack
- ✅ **Cached Dependencies**: GitHub Actions caches pip packages
- ✅ **Parallel Safe**: Tests can run in parallel

## Running Tests

### Local Development
```bash
# Standard tests (PostgreSQL)
python manage.py test

# Fast tests (optimized settings)
python run_fast_tests.py
```

### CI/CD
```bash
# Automatically uses test_settings.py
python run_fast_tests.py
```

## Test Database Impact on CI

### ✅ Benefits
- **No External Dependencies**: No PostgreSQL service needed in CI
- **Fast Execution**: In-memory database is extremely fast
- **Zero Setup**: No database configuration required
- **Cost Effective**: No cloud database costs for testing

### ⚠️ Considerations
- **Different Engine**: SQLite vs PostgreSQL (minimal impact for basic tests)
- **ArrayField Compatibility**: Handled by keeping PostgreSQL locally
- **Production Parity**: Local tests still use PostgreSQL for accuracy

## Workflow Impact

The test suite is optimized for GitHub Actions and will:
1. **Cache pip dependencies** (faster subsequent runs)
2. **Use SQLite in-memory** (no setup time)
3. **Run in ~15-20 seconds** (vs 45s locally)
4. **Require no external services** (fully self-contained)

This configuration provides the best balance of speed for CI while maintaining production database compatibility for local development.