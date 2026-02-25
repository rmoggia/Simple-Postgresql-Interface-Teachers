from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash, g
from config import Config
import db as database
import json

app = Flask(__name__)
app.config.from_object(Config)
app.teardown_appcontext(database.close_connection)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'db_creds' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─── AUTH ────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'db_creds' in session:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        host = request.form.get('host', 'localhost').strip()
        port = request.form.get('port', '5432').strip()
        dbname = request.form.get('dbname', '').strip()
        user = request.form.get('user', '').strip()
        password = request.form.get('password', '')

        ok, err = database.test_connection(host, port, dbname, user, password)
        if ok:
            session['db_creds'] = {
                'host': host, 'port': port,
                'dbname': dbname, 'user': user, 'password': password
            }
            return redirect(url_for('dashboard'))
        else:
            error = err

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        schemas = database.get_schemas()
        schema = request.args.get('schema', schemas[0] if schemas else 'public')
        tables = database.get_tables(schema)
        return render_template('dashboard.html',
                               schemas=schemas, current_schema=schema, tables=tables,
                               creds=session['db_creds'])
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('logout'))


# ─── TABLE VIEW ──────────────────────────────────────────────────────────────

@app.route('/table/<schema>/<table>')
@login_required
def table_view(schema, table):
    try:
        page = int(request.args.get('page', 1))
        order_col = request.args.get('order_col')
        order_dir = request.args.get('order_dir', 'ASC')
        per_page = 50

        columns = database.get_table_columns(schema, table)
        pk_cols = database.get_primary_keys(schema, table)
        rows, total = database.get_table_data(schema, table, page, per_page, order_col, order_dir)
        total_pages = (total + per_page - 1) // per_page

        return render_template('table_view.html',
                               schema=schema, table=table,
                               columns=columns, rows=rows,
                               pk_cols=pk_cols,
                               page=page, total_pages=total_pages, total=total,
                               order_col=order_col, order_dir=order_dir)
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('dashboard'))


# ─── INSERT ROW ──────────────────────────────────────────────────────────────

@app.route('/table/<schema>/<table>/insert', methods=['GET', 'POST'])
@login_required
def insert_row(schema, table):
    columns = database.get_table_columns(schema, table)
    if request.method == 'POST':
        data = {}
        for col in columns:
            val = request.form.get(col[0], '').strip()
            if val != '':
                data[col[0]] = val
        try:
            database.insert_row(schema, table, data)
            flash('Riga inserita con successo.', 'success')
            return redirect(url_for('table_view', schema=schema, table=table))
        except Exception as e:
            flash(str(e), 'error')
    return render_template('row_form.html', schema=schema, table=table,
                           columns=columns, row=None, action='insert')


# ─── EDIT ROW ────────────────────────────────────────────────────────────────

@app.route('/table/<schema>/<table>/edit', methods=['GET', 'POST'])
@login_required
def edit_row(schema, table):
    pk_cols = database.get_primary_keys(schema, table)
    columns = database.get_table_columns(schema, table)

    # Read PK values from query string
    pk_vals = [request.args.get(f'pk_{k}') or request.form.get(f'pk_{k}') for k in pk_cols]

    if request.method == 'POST':
        data = {}
        for col in columns:
            val = request.form.get(col[0], '').strip()
            data[col[0]] = val if val != '' else None
        try:
            database.update_row(schema, table, pk_cols, pk_vals, data)
            flash('Riga aggiornata con successo.', 'success')
            return redirect(url_for('table_view', schema=schema, table=table))
        except Exception as e:
            flash(str(e), 'error')

    # Fetch current row
    row_data = {}
    rows, _ = database.get_table_data(schema, table, 1, 9999)
    for r in rows:
        if all(str(r.get(k)) == str(v) for k, v in zip(pk_cols, pk_vals)):
            row_data = dict(r)
            break

    return render_template('row_form.html', schema=schema, table=table,
                           columns=columns, row=row_data, action='edit',
                           pk_cols=pk_cols, pk_vals=pk_vals)


# ─── DELETE ROW ──────────────────────────────────────────────────────────────

@app.route('/table/<schema>/<table>/delete', methods=['POST'])
@login_required
def delete_row(schema, table):
    pk_cols = database.get_primary_keys(schema, table)
    pk_vals = [request.form.get(f'pk_{k}') for k in pk_cols]
    try:
        database.delete_row(schema, table, pk_cols, pk_vals)
        flash('Riga eliminata.', 'success')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('table_view', schema=schema, table=table))


# ─── SQL QUERY EDITOR ────────────────────────────────────────────────────────

@app.route('/query', methods=['GET', 'POST'])
@login_required
def query():
    result = None
    error = None
    sql = ''
    if request.method == 'POST':
        sql = request.form.get('sql', '').strip()
        try:
            result = database.execute_query(sql)
        except Exception as e:
            error = str(e)
    return render_template('query.html', result=result, error=error, sql=sql)


# ─── STRUCTURE MANAGER ───────────────────────────────────────────────────────

@app.route('/structure/<schema>/<table>')
@login_required
def structure(schema, table):
    columns = database.get_table_columns(schema, table)
    pk_cols = database.get_primary_keys(schema, table)
    return render_template('structure.html', schema=schema, table=table,
                           columns=columns, pk_cols=pk_cols)


@app.route('/structure/ddl', methods=['POST'])
@login_required
def execute_ddl():
    sql = request.form.get('sql', '').strip()
    ok, err = database.execute_ddl(sql)
    if ok:
        flash('Operazione eseguita con successo.', 'success')
    else:
        flash(f'Errore DDL: {err}', 'error')
    return redirect(request.referrer or url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
