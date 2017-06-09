from appconfig import connection_string, status_codes, format_time
import psycopg2
import psycopg2.extras

CREATE_FORUM_SQL = """INSERT INTO forums ("user", slug, title)
						VALUES ((SELECT nickname FROM users WHERE nickname = %(user)s), 
						%(slug)s, %(title)s) RETURNING *"""

GET_FORUM_SQL = """SELECT * FROM forums WHERE slug = %(slug)s"""


def get_threads_sql(since, desc):
	sql = "SELECT * FROM threads WHERE forum = %(forum)s"
	if since is not None:
		sql += " AND created "
		sql += "<= %(since)s" if desc else ">= %(since)s"
	sql += " ORDER BY created"
	if desc:
		sql += " DESC"
	sql += " LIMIT %(limit)s"
	return sql


class ForumDbManager:
	@staticmethod
	def create(content):
		connection = None
		code = status_codes['CREATED']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(CREATE_FORUM_SQL, content)
			content = cursor.fetchone()
			connection.commit()
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['CONFLICT']
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_FORUM_SQL, {'slug': content['slug']})
			content = cursor.fetchone()
			if content is None:
				code = status_codes['NOT_FOUND']
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['NOT_FOUND']
			content = None
		finally:
			if connection:
				connection.close()
		return content, code

	@staticmethod
	def get(slug):
		connection = None
		content = None
		code = status_codes['OK']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_FORUM_SQL, {'slug': slug})
			content = cursor.fetchone()
			if content is None:
				code = status_codes['NOT_FOUND']
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
		finally:
			if connection:
				connection.close()
		return content, code

	@staticmethod
	def get_threads(slug, limit, since, desc):
		connection = None
		content = None
		code = status_codes['OK']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(get_threads_sql(since=since, desc=desc), {'forum': slug, 'since': since, 'limit': limit})
			content = cursor.fetchall()
			for param in content:
				param['created'] = format_time(param['created'])
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['NOT_FOUND']
		finally:
			if connection:
				connection.close()
		return content, code

	@staticmethod
	def get_users(slug, limit, since, desc):
		pass

	@staticmethod
	def count():
		pass

	@staticmethod
	def clear():
		pass
