from appconfig import connection_string, status_codes
import psycopg2
import psycopg2.extras

CREATE_USER_SQL = """INSERT INTO users (about, email, fullname, nickname) 
					VALUES(%(about)s, %(email)s, %(fullname)s, %(nickname)s)"""

GET_USER_SQL = """SELECT about, email, fullname, nickname 
					FROM users WHERE nickname = %(nickname)s OR email = %(email)s"""


def update_user_sql(user):
	sql = 'UPDATE users SET'
	sql += ' about = %(about)s,' if 'about' in user else ' about = about,'
	sql += ' email = %(email)s,' if 'email' in user else ' email = email,'
	sql += ' fullname = %(fullname)s' if 'fullname' in user else ' fullname = fullname'
	sql += ' WHERE nickname = %(nickname)s RETURNING *'
	return sql


class UserDbManager:
	@staticmethod
	def create(user):
		connection = None
		code = status_codes['CREATED']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor()
			cursor.execute(CREATE_USER_SQL, user)
			connection.commit()
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['CONFLICT']
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_USER_SQL, {'nickname': user['nickname'], 'email': user['email']})
			user = cursor.fetchall()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['NOT_FOUND']
			user = None
		finally:
			if connection:
				connection.close()
		return user, code

	@staticmethod
	def get(nickname):
		connection = None
		user = None
		code = status_codes['OK']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_USER_SQL, {'nickname': nickname, 'email': None})
			user = cursor.fetchone()
			if user is None:
				code = status_codes['NOT_FOUND']
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
		finally:
			if connection:
				connection.close()
		return user, code

	@staticmethod
	def update(user):
		connection = None
		code = status_codes['OK']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(update_user_sql(user), user)
			user = cursor.fetchone()
			if user is None:
				code = status_codes['NOT_FOUND']
			connection.commit()
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['CONFLICT']
			user = None
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['NOT_FOUND']
			user = None
		finally:
			if connection:
				connection.close()
		return user, code

	@staticmethod
	def count():
		pass

	@staticmethod
	def clear():
		pass
