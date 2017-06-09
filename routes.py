from flask import jsonify, request
from appconfig import app, status_codes
from database.userdb import UserDbManager
from database.forumdb import ForumDbManager
from database.threaddb import ThreadDbManager

user_db = UserDbManager()
forum_db = ForumDbManager()
thread_db = ThreadDbManager()


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
