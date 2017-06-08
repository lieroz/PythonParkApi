from flask import jsonify, request
from appconfig import app
from database.userdb import UserDbManager

user_db = UserDbManager()


@app.route('/api/user/<nickname>/create', methods=['POST'])
def create_user(nickname):
	content = request.json
	content['nickname'] = nickname
	user, code = user_db.create(user=content)
	return jsonify(user), code


@app.route('/api/user/<nickname>/profile', methods=['GET', 'POST'])
def view_profile(nickname):
	if request.method == 'GET':
		user, code = user_db.get(nickname=nickname)
	else:
		content = request.json
		content['nickname'] = nickname
		user, code = user_db.update(user=content)
	return jsonify(user), code

