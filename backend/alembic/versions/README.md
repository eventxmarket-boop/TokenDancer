# Alembic Migrations

Migration scripts for all database schema changes.

## Usage

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Check current version
alembic current

# Rollback
alembic downgrade -1
```

## Initial Migration

- `001_initial.py` — Creates all tables: users, products, carts, orders, api_keys, usage_records, redeem_codes, redeem_logs, balance_ledger
