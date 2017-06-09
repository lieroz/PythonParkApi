from flask import jsonify, request
from appconfig import app, format_time
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
