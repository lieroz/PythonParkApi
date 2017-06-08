from flask import Flask, g
from werkzeug.contrib.fixers import ProxyFix
import psycopg2

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
connection_string = 'dbname=%s user=%s host=%s password=%s' % ('testdb', 'lieroz', 'localhost', 'b769sz7u')

status_codes = {
	'OK': 200,
	'CREATED': 201,
	'NOT_FOUND': 404,
	'CONFLICT': 409
}


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


init_db()
