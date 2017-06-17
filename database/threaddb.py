from appconfig import status_codes, format_time, get_db_cursor
import psycopg2
import psycopg2.extras

UPDATE_VOTES_SQL = """SELECT update_or_insert_votes(%(nickname)s, %(thread)s, %(voice)s)"""


def create_thread_sql(content):
	if 'created' not in content:
		sql = """INSERT INTO threads (author, forum, message, slug, title) 
					VALUES (
						(
							SELECT nickname 
							FROM users 
							WHERE nickname = %(author)s
						),  
						(
							SELECT slug
							FROM forums
							WHERE slug = %(forum)s
						), %(message)s, %(slug)s, %(title)s) RETURNING *"""
	else:
		sql = """INSERT INTO threads (author, created, forum, message, slug, title) 
					VALUES (
						(
							SELECT nickname 
							FROM users 
							WHERE nickname = %(author)s
						), %(created)s,
						(
							SELECT slug
							FROM forums
							WHERE slug = %(forum)s
						), %(message)s, %(slug)s, %(title)s) RETURNING *"""
	return sql


def get_thread_sql(slug_or_id):
	if slug_or_id.isdigit():
		sql = "SELECT * FROM threads WHERE id = %(slug_or_id)s"
	else:
		sql = "SELECT * FROM threads WHERE slug = %(slug_or_id)s"
	return sql


def update_thread_sql(content):
	sql = "UPDATE threads SET"
	sql += " message = %(message)s," if 'message' in content else " message = message,"
	sql += " title = %(title)s" if 'title' in content else " title = title"
	sql += " WHERE id = %(slug_or_id)s" if content['slug_or_id'].isdigit() else " WHERE slug = %(slug_or_id)s"
	sql += " RETURNING *"
	return sql


class ThreadDbManager:
	@staticmethod
	def create(content):
		code = status_codes['CREATED']
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(create_thread_sql(content=content), content)
				content = cursor.fetchone()
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			code = status_codes['CONFLICT']
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(get_thread_sql(slug_or_id=content['slug']), {'slug_or_id': content['slug']})
				content = cursor.fetchone()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			code = status_codes['NOT_FOUND']
			content = None
		if content is None:
			code = status_codes['NOT_FOUND']
		else:
			content['created'] = format_time(content['created'])
		return content, code

	@staticmethod
	def update(content):
		code = status_codes['OK']
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(update_thread_sql(content=content), content)
				content = cursor.fetchone()
				if content is None:
					code = status_codes['NOT_FOUND']
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			code = status_codes['CONFLICT']
			content = None
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			code = status_codes['NOT_FOUND']
			content = None
		if content is not None:
			content['created'] = format_time(content['created'])
		return content, code

	@staticmethod
	def get(slug_or_id):
		content = None
		code = status_codes['OK']
		try:
			with get_db_cursor() as cursor:
				cursor.execute(get_thread_sql(slug_or_id=slug_or_id), {'slug_or_id': slug_or_id})
				content = cursor.fetchone()
				if content is None:
					code = status_codes['NOT_FOUND']
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
		if content is None:
			code = status_codes['NOT_FOUND']
		else:
			content['created'] = format_time(content['created'])
		return content, code

	@staticmethod
	def update_votes(content):
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(UPDATE_VOTES_SQL, content)
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)

	@staticmethod
	def count():
		content = None
		try:
			with get_db_cursor() as cursor:
				cursor.execute("SELECT COUNT(*) FROM threads")
				content = cursor.fetchone()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
		return content['count']

	@staticmethod
	def clear():
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute("DELETE FROM threads")
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
