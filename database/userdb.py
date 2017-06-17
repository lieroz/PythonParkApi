from appconfig import status_codes, get_db_cursor
import psycopg2
import psycopg2.extras

CREATE_USER_SQL = """INSERT INTO users (about, email, fullname, nickname) 
					VALUES(%(about)s, %(email)s, %(fullname)s, %(nickname)s)"""

GET_USER_SQL = """SELECT about, email, fullname, nickname 
					FROM users WHERE nickname = %(nickname)s OR email = %(email)s"""


def update_user_sql(content):
	sql = 'UPDATE users SET'
	sql += ' about = %(about)s,' if 'about' in content else ' about = about,'
	sql += ' email = %(email)s,' if 'email' in content else ' email = email,'
	sql += ' fullname = %(fullname)s' if 'fullname' in content else ' fullname = fullname'
	sql += ' WHERE nickname = %(nickname)s RETURNING *'
	return sql


class UserDbManager:
	@staticmethod
	def create(content):
		code = status_codes['CREATED']
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(CREATE_USER_SQL, content)
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			code = status_codes['CONFLICT']
			with get_db_cursor() as cursor:
				cursor.execute(GET_USER_SQL, {'nickname': content['nickname'], 'email': content['email']})
				content = cursor.fetchall()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			code = status_codes['NOT_FOUND']
			content = None
		return content, code

	@staticmethod
	def get(nickname):
		content = None
		code = status_codes['OK']
		try:
			with get_db_cursor() as cursor:
				cursor.execute(GET_USER_SQL, {'nickname': nickname, 'email': None})
				content = cursor.fetchone()
				if content is None:
					code = status_codes['NOT_FOUND']
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
		return content, code

	@staticmethod
	def update(content):
		code = status_codes['OK']
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute(update_user_sql(content=content), content)
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
		return content, code

	@staticmethod
	def count():
		content = None
		try:
			with get_db_cursor() as cursor:
				cursor.execute("SELECT COUNT(*) FROM users")
				content = cursor.fetchone()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
		return content['count']

	@staticmethod
	def clear():
		try:
			with get_db_cursor(commit=True) as cursor:
				cursor.execute("DELETE FROM users")
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
