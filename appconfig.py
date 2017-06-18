import os
from contextlib import contextmanager
from urllib.parse import urlparse

from flask import Flask, g
from psycopg2.pool import ThreadedConnectionPool
import psycopg2
import psycopg2.extras
import pytz

app = Flask(__name__)
connection_string = 'dbname=%s user=%s host=%s password=%s' % ('docker', 'docker', 'localhost', 'docker')

status_codes = {
	'OK': 200,
	'CREATED': 201,
	'NOT_FOUND': 404,
	'CONFLICT': 409
}

url = urlparse(os.environ.get('DATABASE_URL'))
pool = ThreadedConnectionPool(
	1, 8, database='docker', user='docker', password='docker', host='localhost', port='5432'
)


@contextmanager
def get_db_connection():
	try:
		connection = pool.getconn()
		yield connection
	finally:
		pool.putconn(connection)


@contextmanager
def get_db_cursor(commit=False):
	with get_db_connection() as connection:
		cursor = connection.cursor(
			cursor_factory=psycopg2.extras.RealDictCursor)
		try:
			yield cursor
			if commit:
				connection.commit()
		finally:
			cursor.close()


def format_time(created):
	zone = pytz.timezone('Europe/Moscow')
	if created.tzinfo is None:
		created = zone.localize(created)
	utc_time = created.astimezone(pytz.utc)
	utc_str = utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
	utc_str = utc_str[:-3] + 'Z'
	return utc_str


@app.teardown_appcontext
def close_connection(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()


def init_db():
	with app.app_context():
		db = getattr(g, '_database', None)
		if db is None:
			db = g._database = psycopg2.connect(connection_string)
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().execute(f.read())
		db.commit()


# init_db()
