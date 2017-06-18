from flask import jsonify, request
from appconfig import app, status_codes, format_time
from datetime import datetime
from database.userdb import UserDbManager
from database.forumdb import ForumDbManager
from database.threaddb import ThreadDbManager
from database.postsdb import PostsDbManager

user_db = UserDbManager()
forum_db = ForumDbManager()
thread_db = ThreadDbManager()
posts_db = PostsDbManager()


@app.route('/api/user/<nickname>/create', methods=['POST'])
def create_user(nickname):
	content = request.json
	content['nickname'] = nickname
	user, code = user_db.create(content=content)
	return jsonify(user), code


@app.route('/api/user/<nickname>/profile', methods=['GET', 'POST'])
def view_profile(nickname):
	if request.method == 'GET':
		user, code = user_db.get(nickname=nickname)
	else:
		content = request.json
		content['nickname'] = nickname
		user, code = user_db.update(content=content)
	return jsonify(user), code


@app.route('/api/forum/create', methods=['POST'])
def create_forum():
	content = request.json
	forum, code = forum_db.create(content=content)
	return jsonify(forum), code


@app.route('/api/forum/<slug>/details', methods=['GET'])
def view_forum_info(slug):
	forum, code = forum_db.get(slug=slug)
	return jsonify(forum), code


@app.route('/api/forum/<slug>/create', methods=['POST'])
def create_thread(slug):
	content = request.json
	content['forum'] = slug
	if 'slug' not in content:
		content['slug'] = None
	thread, code = thread_db.create(content=content)
	return jsonify(thread), code


@app.route('/api/forum/<slug>/threads', methods=['GET'])
def get_forum_threads(slug):
	query_params = request.args.to_dict()
	limit, since, desc = 100, None, False
	for key in query_params.keys():
		if key == 'limit':
			limit = query_params['limit']
		elif key == 'since':
			since = query_params['since']
		elif key == 'desc':
			if query_params[key] == 'true':
				desc = True
	forum, code = forum_db.get(slug=slug)
	if code == status_codes['NOT_FOUND']:
		return jsonify([]), code
	threads, code = forum_db.get_threads(slug=slug, limit=limit, since=since, desc=desc)
	return jsonify(threads), code


@app.route('/api/thread/<slug_or_id>/create', methods=['POST'])
def create_posts(slug_or_id):
	posts = request.json
	if not posts:
		return jsonify(None), status_codes['NOT_FOUND']
	thread, code = thread_db.get(slug_or_id=slug_or_id)
	if code == status_codes['NOT_FOUND']:
		return jsonify(None), code
	forum, code = forum_db.get(slug=thread['forum'])
	if code == status_codes['NOT_FOUND']:
		return jsonify(None), code
	created = format_time(datetime.now())
	data = []
	for post in posts:
		post_id = posts_db.get_id()
		if 'parent' not in post:
			data.append(
				(post['author'], created, forum['slug'], post_id, post['message'], 0, thread['id'], [post_id], post_id))
		else:
			parent, code = posts_db.get(post['parent'])
			if code == status_codes['NOT_FOUND'] or thread['id'] != parent['thread']:
				return jsonify(None), status_codes['CONFLICT']
			path = posts_db.get_path(parent=post['parent'])
			path.append(post_id)
			data.append(
				(post['author'], created, forum['slug'], post_id, post['message'], post['parent'], thread['id'], path, path[0]))
		post['created'] = created
		post['forum'] = forum['slug']
		post['id'] = post_id
		post['thread'] = thread['id']
	code = posts_db.create(data=data, forum=thread['forum'])
	if code == status_codes['CREATED']:
		return jsonify(posts), code
	return jsonify(None), code


@app.route('/api/thread/<slug_or_id>/vote', methods=['POST'])
def vote(slug_or_id):
	content = request.json
	thread, code = thread_db.get(slug_or_id=slug_or_id)
	if code == status_codes['NOT_FOUND']:
		return jsonify(None), code
	user, code = user_db.get(nickname=content['nickname'])
	if code == status_codes['NOT_FOUND']:
		return jsonify(None), code
	content['thread'] = thread['id']
	thread_db.update_votes(content=content)
	thread, code = thread_db.get(slug_or_id=slug_or_id)
	return jsonify(thread), code


@app.route('/api/thread/<slug_or_id>/details', methods=['GET', 'POST'])
def view_thread(slug_or_id):
	if request.method == 'GET':
		thread, code = thread_db.get(slug_or_id=slug_or_id)
	else:
		content = request.json
		content['slug_or_id'] = slug_or_id
		thread, code = thread_db.update(content=content)
	return jsonify(thread), code


@app.route('/api/thread/<slug_or_id>/posts', methods=['GET'])
def get_posts_sorted(slug_or_id):
	query_params = request.args.to_dict()
	limit, marker, sort, desc = 100, '0', 'flat', False
	for key in query_params.keys():
		if key == 'limit':
			limit = query_params['limit']
		elif key == 'marker':
			marker = query_params['marker']
		elif key == 'sort':
			sort = query_params['sort']
		elif key == 'desc':
			if query_params[key] == 'true':
				desc = True
	posts, code = posts_db.sort(limit=limit, offset=marker, sort=sort, desc=desc, slug_or_id=slug_or_id)
	if not posts and marker == '0':
		return jsonify(None), status_codes['NOT_FOUND']
	if not posts:
		return jsonify({'marker': marker, 'posts': posts}), code
	return jsonify({'marker': str(int(marker) + int(limit)), 'posts': posts}), code


@app.route('/api/forum/<slug>/users', methods=['GET'])
def get_forum_users(slug):
	query_params = request.args.to_dict()
	limit, since, desc = 100, None, False
	for key in query_params.keys():
		if key == 'limit':
			limit = query_params['limit']
		elif key == 'since':
			since = query_params['since']
		elif key == 'desc':
			if query_params[key] == 'true':
				desc = True
	forum, code = forum_db.get(slug=slug)
	if code == status_codes['NOT_FOUND']:
		return jsonify(None), code
	threads, code = forum_db.get_users(slug=slug, limit=limit, since=since, desc=desc)
	return jsonify(threads), code


@app.route('/api/post/<identifier>/details', methods=['GET', 'POST'])
def get_post_detailed(identifier):
	if request.method == 'GET':
		related = request.args.getlist('related')
		post, code = posts_db.get(identifier=identifier)
		if post is None:
			return jsonify(None), status_codes['NOT_FOUND']
		user = None
		forum = None
		thread = None
		for i in related:
			for j in i.split(','):
				if j == 'user':
					user, code = user_db.get(nickname=post['author'])
				if j == 'forum':
					forum, code = forum_db.get(slug=post['forum'])
				if j == 'thread':
					thread, code = thread_db.get(slug_or_id=str(post['thread']))
		return jsonify({'author': user, 'forum': forum, 'post': post, 'thread': thread}), code
	elif request.method == 'POST':
		content = request.json
		post, code = posts_db.get(identifier=identifier)
		if post is not None:
			if 'message' in content and post['message'] != content['message']:
				post, code = posts_db.update(identifier=identifier, content=content)
		return jsonify(post), code


@app.route('/api/service/status', methods=['GET'])
def status():
	return jsonify(
		{
			'forum': forum_db.count(),
			'post': posts_db.count(),
			'thread': thread_db.count(),
			'user': user_db.count()
		}
	), status_codes['OK']


@app.route('/api/service/clear', methods=['POST'])
def clear():
	user_db.clear()
	thread_db.clear()
	forum_db.clear()
	posts_db.clear()
	return jsonify(None), status_codes['OK']
