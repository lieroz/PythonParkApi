from appconfig import connection_string, status_codes
import psycopg2
import psycopg2.extras

CREATE_FORUM_SQL = """INSERT INTO forums ("user", slug, title)
						VALUES (%(user)s, %(slug)s, %(title)s) RETURNING *"""

GET_FORUM_SQL = """SELECT * FROM forums WHERE slug = %(slug)s"""


class ForumDbManager:
	@staticmethod
	def create(forum):
		connection = None
		code = status_codes['CREATED']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(CREATE_FORUM_SQL, forum)
			forum = cursor.fetchone()
			connection.commit()
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['CONFLICT']
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_FORUM_SQL, {'slug': forum['slug']})
			forum = cursor.fetchone()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['NOT_FOUND']
			forum = None
		finally:
			if connection:
				connection.close()
		return forum, code

	@staticmethod
	def get(slug):
		pass

	@staticmethod
	def get_threads(slug, limit, since, desc):
		pass

	@staticmethod
	def get_users(slug, limit, since, desc):
		pass

	@staticmethod
	def count():
		pass

	@staticmethod
	def clear():
		pass
