# db

Database utilities.

## connection_check.py

Validate a PostgreSQL connection URI and check whether the database is reachable.

### Functions

#### `parse_and_validate_uri(uri: str) -> ConnectionCheckResult`

Validates the *format* of a PostgreSQL URI. **No network call is made.**
Checks that the scheme is `postgresql`/`postgres` and that a host and database
name are present.

#### `check_postgres_connection(uri: str, timeout: float = 5.0) -> ConnectionCheckResult`

Validates the URI format, then attempts to open a connection (with a bounded
`timeout`, default 5 seconds) and run `SELECT 1`. Never raises for
connection/format problems — returns a structured result dict instead.

### Result schema

```python
{
    "uri_valid": bool,        # did the URI pass format validation?
    "reachable": bool,        # did we connect and run the test query?
    "error": str | None,      # human-readable error, or None on success
    "detail": {               # parsed URI pieces
        "scheme": str | None,
        "host": str | None,
        "port": int | None,
        "dbname": str | None,
        "username": str | None,
    },
}
```

Invariant: `reachable=True` implies `error is None`.

### Dependencies

- Standard library only for format validation.
- `psycopg2` (install `psycopg2-binary`) is required **only** for the
  reachability check. It is imported lazily; if missing, the reachability
  check returns a clear error while format validation still works.

### Example

See `db/examples/connection_check_example.py`. It uses synthetic URIs only
and targets an RFC 5737 test address (`192.0.2.1`) for the reachability demo,
so no real database is contacted.

```python
from db.connection_check import check_postgres_connection

result = check_postgres_connection("postgresql://user:pass@localhost:5432/mydb")
if result["uri_valid"] and result["reachable"]:
    print("Database is reachable.")
else:
    print("Problem:", result["error"])
```

### Validation

Validator: `tests/test_connection_check.py` (synthetic data only). Run with:

```
python tests/test_connection_check.py
```
