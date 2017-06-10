from appconfig import connection_string, status_codes, format_time
import psycopg2
import psycopg2.extras

CREATE_POSTS_SQL = \
	"""INSERT INTO posts (author, created, forum, message, parent, thread, path, root_id)
		VALUES (
			%(author)s, %(created)s, %(forum)s, %(message)s, %(parent)s, %(thread)s, array_append(
				%(path)s, %(id)s
			), %(root_id)s)"""

GET_PATH_SQL = """SELECT path FROM posts WHERE id = %(parent)s"""

GET_NEXTVAL_SQL = """SELECT nextval('posts_id_seq')"""

GET_POST_SQL = """SELECT * FROM posts WHERE id = %(id)s"""


def posts_flat_sort_sql(slug_or_id, desc):
	sql = "SELECT author, created, forum, id, isEdited, message, parent, thread FROM posts WHERE thread = "
	if slug_or_id.isdigit():
		sql += "%(slug_or_id)s"
	else:
		sql += "(SELECT id FROM threads WHERE slug = %(slug_or_id)s)"
	sql += " ORDER BY created"
	if desc:
		sql += " DESC"
	sql += ", id"
	if desc:
		sql += " DESC"
	sql += " LIMIT %(limit)s OFFSET %(offset)s"
	return sql


def posts_tree_sort_sql(slug_or_id, desc):
	sql = "SELECT author, created, forum, id, isEdited, message, parent, thread FROM posts WHERE thread = "
	if slug_or_id.isdigit():
		sql += "%(slug_or_id)s"
	else:
		sql += "(SELECT id FROM threads WHERE slug = %(slug_or_id)s)"
	sql += " ORDER BY path"
	if desc:
		sql += " DESC"
	sql += " LIMIT %(limit)s OFFSET %(offset)s"
	return sql


def posts_parent_tree_sort_sql(slug_or_id, desc):
	sql = """SELECT author, created, forum, id, isEdited, message, parent, thread 
				FROM posts 
				WHERE root_id IN (
					SELECT id
					FROM posts
					WHERE thread = """
	if slug_or_id.isdigit():
		sql += "%(slug_or_id)s"
	else:
		sql += "(SELECT id FROM threads WHERE slug = %(slug_or_id)s)"
	sql += " AND parent = 0 ORDER BY id"
	if desc:
		sql += " DESC"
	sql += " LIMIT %(limit)s OFFSET %(offset)s)"
	sql += " ORDER BY path"
	if desc:
		sql += " DESC"
	return sql


class PostsDbManager:
	@staticmethod
	def get_id():
		connection = None
		content = None
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_NEXTVAL_SQL)
			content = cursor.fetchone()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
		finally:
			if connection:
				connection.close()
		return content['nextval']

	@staticmethod
	def get_path(parent):
		connection = None
		content = None
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_PATH_SQL, {'parent': parent})
			content = cursor.fetchone()
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
		finally:
			if connection:
				connection.close()
		return content['path']

	@staticmethod
	def create(posts):
		connection = None
		code = status_codes['CREATED']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.executemany(CREATE_POSTS_SQL, posts)
			connection.commit()
		except psycopg2.IntegrityError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['CONFLICT']
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
			code = status_codes['NOT_FOUND']
		finally:
			if connection:
				connection.close()
		return code

	@staticmethod
	def update(content):
		pass

	@staticmethod
	def get(identifier):
		connection = None
		content = None
		code = status_codes['OK']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			cursor.execute(GET_POST_SQL, {'id': identifier})
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
	def get_detailed(content, slug_or_id):
		pass

	@staticmethod
	def sort(limit, offset, sort, desc, slug_or_id):
		connection = None
		content = None
		code = status_codes['OK']
		try:
			connection = psycopg2.connect(connection_string)
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
			params = {'slug_or_id': slug_or_id, 'limit': limit, 'offset': offset}
			if sort == 'flat':
				cursor.execute(posts_flat_sort_sql(slug_or_id=slug_or_id, desc=desc), params)
			elif sort == 'tree':
				cursor.execute(posts_tree_sort_sql(slug_or_id=slug_or_id, desc=desc), params)
			elif sort == 'parent_tree':
				cursor.execute(posts_parent_tree_sort_sql(slug_or_id=slug_or_id, desc=desc), params)
			content = cursor.fetchall()
			for param in content:
				param['created'] = format_time(param['created'])
		except psycopg2.DatabaseError as e:
			print('Error %s' % e)
			if connection:
				connection.rollback()
		finally:
			if connection:
				connection.close()
		return content, code

	@staticmethod
	def count():
		pass

	@staticmethod
	def clear():
		pass
