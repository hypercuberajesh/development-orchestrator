"""PostgreSQL connection URI validation and reachability checking.

This module provides helpers to (1) validate the *format* of a PostgreSQL
connection URI and (2) check whether the database is actually *reachable*.

The public function never raises on connection problems; it returns a
structured result dict so callers can branch on clear status fields.
"""

from __future__ import annotations

from typing import Optional, TypedDict
from urllib.parse import urlparse, unquote


# Accepted URI schemes for PostgreSQL.
_VALID_SCHEMES = {"postgresql", "postgres"}


class ConnectionCheckResult(TypedDict):
    """Structured result of a PostgreSQL connection check.

    Attributes:
        uri_valid: True if the URI passed format validation.
        reachable: True if a connection was opened and a test query ran.
        error: Human-readable error message, or None on full success.
        detail: Parsed URI pieces (scheme, host, port, dbname, username).
    """

    uri_valid: bool
    reachable: bool
    error: Optional[str]
    detail: dict


def parse_and_validate_uri(uri: str) -> ConnectionCheckResult:
    """Validate the format of a PostgreSQL connection URI.

    This does NOT open a network connection. It only checks that the URI
    is well formed and contains the pieces PostgreSQL needs.

    Args:
        uri: The connection URI, e.g.
            "postgresql://user:pass@localhost:5432/mydb".

    Returns:
        A ConnectionCheckResult with ``reachable`` always False (no network
        attempt was made here) and ``uri_valid`` reflecting the format check.

    Raises:
        TypeError: If ``uri`` is not a string.
    """
    if not isinstance(uri, str):
        raise TypeError(f"uri must be a str, got {type(uri).__name__}")

    detail: dict = {
        "scheme": None,
        "host": None,
        "port": None,
        "dbname": None,
        "username": None,
    }

    stripped = uri.strip()
    if not stripped:
        return ConnectionCheckResult(
            uri_valid=False,
            reachable=False,
            error="URI is empty.",
            detail=detail,
        )

    try:
        parsed = urlparse(stripped)
    except ValueError as exc:
        return ConnectionCheckResult(
            uri_valid=False,
            reachable=False,
            error=f"URI could not be parsed: {exc}",
            detail=detail,
        )

    scheme = (parsed.scheme or "").lower()
    host = parsed.hostname
    port = parsed.port  # may raise ValueError for bad ports -> handled below
    # dbname is the path without the leading slash.
    dbname = unquote(parsed.path.lstrip("/")) if parsed.path else ""
    username = unquote(parsed.username) if parsed.username else None

    detail.update(
        {
            "scheme": scheme or None,
            "host": host,
            "port": port,
            "dbname": dbname or None,
            "username": username,
        }
    )

    if scheme not in _VALID_SCHEMES:
        return ConnectionCheckResult(
            uri_valid=False,
            reachable=False,
            error=(
                f"Invalid scheme '{parsed.scheme}'. "
                f"Expected one of: {sorted(_VALID_SCHEMES)}."
            ),
            detail=detail,
        )

    if not host:
        return ConnectionCheckResult(
            uri_valid=False,
            reachable=False,
            error="URI is missing a host.",
            detail=detail,
        )

    if not dbname:
        return ConnectionCheckResult(
            uri_valid=False,
            reachable=False,
            error="URI is missing a database name.",
            detail=detail,
        )

    return ConnectionCheckResult(
        uri_valid=True,
        reachable=False,
        error=None,
        detail=detail,
    )


def check_postgres_connection(
    uri: str,
    timeout: float = 5.0,
) -> ConnectionCheckResult:
    """Validate a PostgreSQL URI and check that the database is reachable.

    First validates the URI format. If valid, attempts to open a connection
    with a bounded timeout and run a trivial ``SELECT 1`` query. This function
    never raises for connection/format problems; it returns a result dict.

    Args:
        uri: The PostgreSQL connection URI.
        timeout: Connection timeout in seconds. Must be > 0.

    Returns:
        A ConnectionCheckResult. ``reachable`` is True only if the connection
        opened and the test query succeeded.

    Raises:
        TypeError: If ``uri`` is not a string.
        ValueError: If ``timeout`` is not a positive number.
    """
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
        raise ValueError("timeout must be a positive number.")
    if timeout <= 0:
        raise ValueError("timeout must be greater than 0.")

    result = parse_and_validate_uri(uri)
    if not result["uri_valid"]:
        return result

    # Lazily import the driver so format validation works without it.
    try:
        import psycopg2  # type: ignore
    except ImportError:
        return ConnectionCheckResult(
            uri_valid=True,
            reachable=False,
            error=(
                "psycopg2 is not installed. Install it with "
                "'pip install psycopg2-binary' to check reachability."
            ),
            detail=result["detail"],
        )

    conn = None
    try:
        conn = psycopg2.connect(uri, connect_timeout=int(max(1, round(timeout))))
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
    except Exception as exc:  # psycopg2.OperationalError and friends
        return ConnectionCheckResult(
            uri_valid=True,
            reachable=False,
            error=f"Could not reach database: {exc}".strip(),
            detail=result["detail"],
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    return ConnectionCheckResult(
        uri_valid=True,
        reachable=True,
        error=None,
        detail=result["detail"],
    )
