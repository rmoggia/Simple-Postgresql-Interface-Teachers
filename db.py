import psycopg2
import psycopg2.extras
from flask import session, g
import re


def get_connection():
    """Get a database connection using session credentials."""
    if 'db_conn' not in g:
        creds = session.get('db_creds')
        if not creds:
            raise Exception("Nessuna credenziale di connessione trovata.")
        try:
            g.db_conn = psycopg2.connect(
                host=creds['host'],
                port=creds['port'],
                dbname=creds['dbname'],
                user=creds['user'],
                password=creds['password'],
                connect_timeout=5
            )
            g.db_conn.autocommit = False
        except psycopg2.OperationalError as e:
            raise Exception(f"Errore di connessione: {str(e)}")
    return g.db_conn


def close_connection(e=None):
    """Close the database connection at end of request."""
    conn = g.pop('db_conn', None)
    if conn is not None:
        conn.close()


def test_connection(host, port, dbname, user, password):
    """Test a connection with given credentials."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=5
        )
        conn.close()
        return True, None
    except psycopg2.OperationalError as e:
        return False, str(e)


def get_schemas():
    """Get list of non-system schemas."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
              AND schema_name NOT LIKE 'pg_%'
            ORDER BY schema_name
        """)
        return [row[0] for row in cur.fetchall()]


def get_tables(schema='public'):
    """Get list of tables in a schema."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
        """, (schema,))
        return cur.fetchall()


def get_table_columns(schema, table):
    """Get column definitions for a table."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table))
        return cur.fetchall()


def get_primary_keys(schema, table):
    """Get primary key columns for a table."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = %s
              AND tc.table_name = %s
        """, (schema, table))
        return [row[0] for row in cur.fetchall()]


def get_table_data(schema, table, page=1, per_page=50, order_col=None, order_dir='ASC'):
    """Get paginated data from a table."""
    conn = get_connection()
    # Sanitize identifiers to prevent injection
    safe_schema = re.sub(r'[^\w]', '', schema)
    safe_table = re.sub(r'[^\w]', '', table)
    offset = (page - 1) * per_page

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Count total rows
        cur.execute(f'SELECT COUNT(*) FROM "{safe_schema}"."{safe_table}"')
        total = cur.fetchone()['count']

        # Build ORDER BY clause
        order_clause = ''
        if order_col:
            safe_col = re.sub(r'[^\w]', '', order_col)
            safe_dir = 'DESC' if order_dir.upper() == 'DESC' else 'ASC'
            order_clause = f'ORDER BY "{safe_col}" {safe_dir}'

        cur.execute(f'SELECT * FROM "{safe_schema}"."{safe_table}" {order_clause} LIMIT %s OFFSET %s',
                    (per_page, offset))
        rows = cur.fetchall()

    return rows, int(total)


def execute_query(sql):
    """Execute an arbitrary SQL query and return results."""
    conn = get_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        # Check if it's a SELECT-like query
        if cur.description:
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            conn.commit()
            return {'type': 'select', 'columns': columns, 'rows': rows, 'rowcount': len(rows)}
        else:
            conn.commit()
            return {'type': 'modify', 'rowcount': cur.rowcount}


def insert_row(schema, table, data):
    """Insert a new row into a table."""
    conn = get_connection()
    safe_schema = re.sub(r'[^\w]', '', schema)
    safe_table = re.sub(r'[^\w]', '', table)
    columns = list(data.keys())
    values = list(data.values())
    col_str = ', '.join(f'"{c}"' for c in columns)
    val_str = ', '.join(['%s'] * len(values))
    sql = f'INSERT INTO "{safe_schema}"."{safe_table}" ({col_str}) VALUES ({val_str})'
    with conn.cursor() as cur:
        cur.execute(sql, values)
    conn.commit()


def update_row(schema, table, pk_cols, pk_vals, data):
    """Update a row identified by primary key."""
    conn = get_connection()
    safe_schema = re.sub(r'[^\w]', '', schema)
    safe_table = re.sub(r'[^\w]', '', table)
    set_parts = [f'"{k}" = %s' for k in data.keys()]
    where_parts = [f'"{k}" = %s' for k in pk_cols]
    sql = f'UPDATE "{safe_schema}"."{safe_table}" SET {", ".join(set_parts)} WHERE {" AND ".join(where_parts)}'
    with conn.cursor() as cur:
        cur.execute(sql, list(data.values()) + list(pk_vals))
    conn.commit()


def delete_row(schema, table, pk_cols, pk_vals):
    """Delete a row identified by primary key."""
    conn = get_connection()
    safe_schema = re.sub(r'[^\w]', '', schema)
    safe_table = re.sub(r'[^\w]', '', table)
    where_parts = [f'"{k}" = %s' for k in pk_cols]
    sql = f'DELETE FROM "{safe_schema}"."{safe_table}" WHERE {" AND ".join(where_parts)}'
    with conn.cursor() as cur:
        cur.execute(sql, list(pk_vals))
    conn.commit()


def execute_ddl(sql):
    """Execute DDL statements (CREATE, ALTER, DROP)."""
    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.autocommit = False
