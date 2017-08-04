import os
import sys
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask.ext.cors import CORS, cross_origin
from flask_sockets import Sockets
from datetime import datetime

app = Flask(__name__)
# connect to SQL database with username, password and address
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

class Users(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text)
	address = db.Column(db.Text)

	def __init__(self, name, address):
		self.name = name
		self.address = address

	def __repr__(self):
		return '<name %r>' % self.name

# Normal HTML landing page
@app.route('/')
def homepage():
	the_time = datetime.now()

	return """
	<h1>Hellow World</h1>
	<p>It is currently {time}.</p>
	""".format(time=the_time)

# Define HTTP API endpoint for external connections from web/mobile apps
@app.route('/user', methods = ['GET'])
@cross_origin()
def get_user():
	print("Loading data file into database...")
	for line in open('data_file.csv'):
		name, address = line.split(',')
		new_user = Users(name, address)
		db.session.add(new_user)

	db.session.commit()
	print("Data commited to database.")

	user_id = request.args.get('user_id')
	user = Users.query.filter_by(id=int(user_id)).first().__dict__
	print(user)

	user_json = {
		name: user['name'],
		address: user['address']
	}
	
	return jsonify(user=user_json)

WS_EVENT_CLIENTS = []
@sockets.route('/event/<app_id>/<client_id>')
def ws_event(ws, app_id=None, client_id=None):
	global WS_EVENT_CLIENTS

	if client_id is not None:
		client_id = client_id.encode('utf-8')

	app_id = app_id.encode('utf-8')

	this_client = {
		'ws_object': ws,
		'app_id': app_id,
		'client_id': client_id
	}

	WS_EVENT_CLIENTS.append(this_client)

	while not ws.closed:
		message = ws.receive()

		if message is None:
			if ws.closed:
				break
			continue

		msg_obj = json.loads(message)
		sender_id = msg_obj['user_id'].encode('utf-8')
		title = msg_obj['title'].encode('utf-8')
		content = msg_obj['content'].encode('utf-8')
		category = msg_obj['category'].encode('utf-8')
		status = 'active'

		out_obj = {
			'id': db_row.id,
			'title': title,
			'object_id': app_id,
			'created_at': db_row.created_at,
			'user_id': client_id,
			'content': content,
			'category': category
		}

	for cl in WS_EVENT_CLIENTS:
		if cl['client_id'] is None:
			cl['ws_object'].send(json.dumps(out_obj))

	WS_EVENT_CLIENTS.remove(this_client)

if __name__ == '__main__':

	print("Starting Python web server")
	app.run(debug=True, use_reloader=True)



