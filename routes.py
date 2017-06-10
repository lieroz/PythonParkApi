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


# TODO add update count in forum
@app.route('/api/thread/<slug_or_id>/create', methods=['POST'])
def create_posts(slug_or_id):
	posts = request.json
	if not posts:
		return status_codes['NOT_FOUND']
	thread, code = thread_db.get(slug_or_id=slug_or_id)
	if code == status_codes['NOT_FOUND']:
		return code
	forum, code = forum_db.get(slug=thread['forum'])
	if code == status_codes['NOT_FOUND']:
		return code
	post_id = posts_db.get_id()
	created = format_time(datetime.now())
	for post in posts:
		post_id += 1
		if 'parent' not in post:
			post['parent'] = 0
			post['path'] = None
			post['root_id'] = post_id
		else:
			parent, code = posts_db.get(post['parent'])
			if code == status_codes['NOT_FOUND'] or thread['id'] != parent['thread']:
				return status_codes['CONFLICT']
			post['path'] = posts_db.get_path(parent=post['parent'])
			post['root_id'] = post['path'][0]
		post['created'] = created
		post['forum'] = forum['slug']
		post['id'] = post_id
		post['thread'] = thread['id']
	code = posts_db.create(posts=posts)
	if code == status_codes['CREATED']:
		return jsonify(posts), code
	return code


@app.route('/api/thread/<slug_or_id>/vote', methods=['POST'])
def vote(slug_or_id):
	thread, code = thread_db.get(slug_or_id=slug_or_id)
	if code == status_codes['NOT_FOUND']:
		return code
	content = request.json
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
	if not posts:
		return jsonify({'marker': marker, 'posts': posts})
	return jsonify({'marker': str(int(marker) + int(limit)), 'posts': posts})
