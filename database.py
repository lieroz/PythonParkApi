from appconfig import connection_string, status_codes
import psycopg2
import psycopg2.extras

CREATE_USER_SQL = """INSERT INTO users (about, email, fullname, nickname) 
					VALUES(%(about)s, %(email)s, %(fullname)s, %(nickname)s)"""

GET_USER_SQL = """SELECT about, email, fullname, nickname 
					FROM users WHERE nickname = %(nickname)s OR email = %(email)s"""


class UserDatabaseManager:
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
			cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
			cursor.execute(GET_USER_SQL, {'nickname': user['nickname'], 'email': user['email']})
			user = cursor.fetchone()
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
			cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
		return user, status_codes['OK']
