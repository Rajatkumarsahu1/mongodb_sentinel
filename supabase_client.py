from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_all(table_name, batch_size=1000, limit=None):
    """Fetch a table in pages. Supabase projects may impose a server row cap."""
    rows = []
    start = 0

    while True:
        end = start + batch_size - 1
        if limit is not None:
            end = min(end, limit - 1)
            if start > end:
                break

        response = (
            supabase.table(table_name)
            .select("*")
            .range(start, end)
            .execute()
        )
        page = response.data or []
        rows.extend(page)

        if not page or len(page) < (end - start + 1):
            break

        start += len(page)
        if limit is not None and len(rows) >= limit:
            break

    return rows[:limit] if limit is not None else rows


def fetch_by_values(table_name, column_name, values, chunk_size=200):
    """Fetch only rows whose key is in values, using small PostgREST IN batches."""
    values = list(values)
    rows = []
    for offset in range(0, len(values), chunk_size):
        chunk = values[offset:offset + chunk_size]
        if not chunk:
            continue
        response = (
            supabase.table(table_name)
            .select("*")
            .in_(column_name, chunk)
            .execute()
        )
        rows.extend(response.data or [])
    return rows
