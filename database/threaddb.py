from appconfig import connection_string, status_codes, format_time
import psycopg2
import psycopg2.extras


def create_thread_sql(content):
	if 'created' not in content:
		sql = """INSERT INTO threads (author, forum, message, slug, title) 
					VALUES (
						(
							SELECT nickname 
							FROM users 
							WHERE nickname = %(author)s
						),  %(forum)s, %(message)s, %(slug)s, %(title)s) RETURNING *"""
	else:
		sql = """INSERT INTO threads (author, created, forum, message, slug, title) 
					VALUES (
						(
							SELECT nickname 
							FROM users 
							WHERE nickname = %(author)s
						), %(created)s, %(forum)s, %(message)s, %(slug)s, %(title)s) RETURNING *"""
	return sql

GET_THREAD_SQL = """SELECT * FROM threads WHERE slug = %(slug)s"""


class ThreadDbManager:
	@staticmethod
	def create(content):
		connection = None
		code = status_codes['CREATED']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(create_thread_sql(content=content), content)
			content = cursor.fetchone()
			connection.commit()
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['CONFLICT']
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_THREAD_SQL, {'slug': content['slug']})
			content = cursor.fetchone()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['NOT_FOUND']
			content = None
		finally:
			if connection:
				connection.close()
		content['created'] = format_time(content['created'])
		return content, code

	@staticmethod
	def update(content):
		pass

	@staticmethod
	def get(slug_or_id):
		pass

	@staticmethod
	def update_votes(content, slug_or_id):
		pass

	@staticmethod
	def count():
		pass

	@staticmethod
	def clear():
		pass
