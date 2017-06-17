from appconfig import status_codes, format_time, get_db_cursor
import psycopg2
import psycopg2.extras

CREATE_FORUM_SQL = """INSERT INTO forums ("user", slug, title)
						VALUES ((SELECT nickname FROM users WHERE nickname = %(user)s), 
						%(slug)s, %(title)s) RETURNING *"""

GET_FORUM_SQL = """SELECT * FROM forums WHERE slug = %(slug)s"""

UPDATE_THREADS_COUNT_SQL = """UPDATE forums SET posts = posts + %(amount)s WHERE slug = %(slug)s"""


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


def get_users_sql(since, desc):
	sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM forum_users WHERE forum = %(forum)s)"
	if since is not None:
		sql += " AND nickname "
		sql += "< %(since)s" if desc else "> %(since)s"
	sql += " ORDER BY nickname COLLATE ucs_basic"
	if desc:
		sql += " DESC"
	sql += " LIMIT %(limit)s"
	return sql


class ForumDbManager:
	@staticmethod
	def create(content):
		code = status_codes['CREATED']
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(CREATE_FORUM_SQL, content)
				content = cursor.fetchone()
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			code = status_codes['CONFLICT']
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(GET_FORUM_SQL, {'slug': content['slug']})
				content = cursor.fetchone()
				if content is None:
					code = status_codes['NOT_FOUND']
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			code = status_codes['NOT_FOUND']
			content = None
		return content, code

	@staticmethod
	def update_thread_count(amount, slug):
		code = status_codes['OK']
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(UPDATE_THREADS_COUNT_SQL, {'amount': amount, 'slug': slug})
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			code = status_codes['NOT_FOUND']
		return code

	@staticmethod
	def get(slug):
		content = None
		code = status_codes['OK']
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(GET_FORUM_SQL, {'slug': slug})
				content = cursor.fetchone()
				if content is None:
					code = status_codes['NOT_FOUND']
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
		return content, code

	@staticmethod
	def get_threads(slug, limit, since, desc):
		content = None
		code = status_codes['OK']
		try:
			with get_db_cursor() as cursor:
				cursor.execute(get_threads_sql(since=since, desc=desc), {'forum': slug, 'since': since, 'limit': limit})
				content = cursor.fetchall()
				for param in content:
					param['created'] = format_time(param['created'])
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			code = status_codes['NOT_FOUND']
		return content, code

	@staticmethod
	def get_users(slug, limit, since, desc):
		content = None
		code = status_codes['OK']
		try:
			with get_db_cursor() as cursor:
				cursor.execute(get_users_sql(since=since, desc=desc), {'forum': slug, 'since': since, 'limit': limit})
				content = cursor.fetchall()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			code = status_codes['NOT_FOUND']
		return content, code

	@staticmethod
	def count():
		content = None
		try:
			with get_db_cursor() as cursor:
				cursor.execute("SELECT COUNT(*) FROM forums")
				content = cursor.fetchone()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
		return content['count']

	@staticmethod
	def clear():
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute("DELETE FROM forums")
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
