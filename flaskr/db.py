import sqlite3
from datetime import datetime

import click
from flask import Flask, current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))

# The code below links the 'init-db' command with the 'flask' command line, allowing to execute 'flask --app flaskr init-db'
@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

# tells Python how to interpret timestamp values in the database. It converts the value to a datetime.datetime
sqlite3.register_converter(
    'timestamp', lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app: Flask):
    # tells Flask to call 'close_db' function when cleaning up after returning a response
    app.teardown_appcontext(close_db)

    # adds a new command that can be called with the 'flask' command
    app.cli.add_command(init_db_command)