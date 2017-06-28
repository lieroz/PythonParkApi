import os
from contextlib import contextmanager
from urllib.parse import urlparse

from flask import Flask
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


def init_db():
	with get_db_cursor(commit=True) as cursor:
		cursor.execute(open('schema.sql', 'r').read())
		cursor.execute("""PREPARE insert_posts_batch AS
						INSERT INTO posts (author, created, forum, id, message, parent, thread, path, root_id) 
						VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""")


init_db()
