from flask import Flask, request, make_response, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from functools import wraps
from flask_mpesa import MpesaAPI
from werkzeug.security import generate_password_hash, check_password_hash
# from ipfs import upload
from blockchain import campaign_payout, create_account, get_balance, confirm_participation, get_accounts_txs
from datetime import datetime, timedelta

import jwt, pytz, json, requests

app = Flask(__name__)
app.config["SECRET_KEY"] = "OQ@FVuEtE2033>Kw73S%xA!dAy#6ey&fppojkK@<f52@mIdQOfIzKBTyQN!eWg6y2uxtM19lGN>5#mzsDEk2BvraxINa41Q+Fc0s!" 
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://bc10b46987ddb0:c6c3c29d@us-cdbr-east-05.cleardb.net/heroku_5ac6ba61392e615?reconnect=true'
app.config["API_ENVIRONMENT"] = "sandbox"
app.config["APP_KEY"] = "Lb0reO3D6ApZbTmhRH8ErSGgOfek9dHq" 
app.config["APP_SECRET"] = "Bc1nN8vOHSxwoBje"

CORS(app, origins=["http://localhost:3000"], supports_credentials = True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mpesa_api=MpesaAPI(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	names = db.Column(db.String(200))
	company_name = db.Column(db.String(200))
	phone = db.Column(db.String(50))
	email = db.Column(db.String(200), nullable=False)
	celo_address = db.Column(db.String(100), nullable=False)
	age = db.Column(db.Integer)
	gender = db.Column(db.Integer)
	location = db.Column(db.String(100))
	logo = db.Column(db.String(100))
	password = db.Column(db.String(500), nullable=False)
	role_id = db.Column(db.Integer, db.ForeignKey('user_roles.id', ondelete='cascade'), nullable=False)


	def __init__(self,role_id, phone, email, password, names=None, company_name=None, age=None, gender=None, location=None):
		self.role_id = role_id
		self.phone = phone
		self.email = email
		self.password = password
		self.names = names
		self.company_name = company_name
		self.age = age
		self.gender = gender
		self.location = location
		self.celo_address = json.dumps(create_account(password))
	
	@property
	def password():
		raise AttributeError('Password not readable')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def encode_auth_token(self, data, time=None):
		'''
		Generate auth token for a user aftere sign up.
		'''
		try:
			payload = {
				'exp': datetime.utcnow() + timedelta(days=30, seconds=0) if not time else time,
				'iat': datetime.utcnow(),
				'sub': data
			}
			
			return jwt.encode(
				payload, 
				current_app.config.get('SECRET_KEY'),
				algorithm='HS256' 
			)
		except Exception as e:
			return e

	@staticmethod
	def decode_auth_token(auth_token):
		try :
			payload = jwt.decode(auth_token, current_app.config.get('SECRET_KEY'), algorithms='HS256')
			return payload['sub']
		except jwt.ExpiredSignatureError:
			return 'Signature expired, sign in again.'
		except jwt.InvalidTokenError:
			return 'Invalid token. Please sign in again.'

	def save(user):
		db.session.add(user)
		try:
			db.session.commit()
			return {"status": True}
		except Exception as e:
			return {"status": False, "message": str(e)}

	def serialize_company(self):
		address = self.celo_address
		address = json.loads(address)
		return{
			'role': "brand",
			'company_name': self.company_name,
			'phone': self.phone,
			'email': self.email,
			'location': self.location,
			'celo_address': f'0x{address["address"]}',
		}

	def serialize_user(self):
		address = self.celo_address
		address = json.loads(address)
		return{
			'role': "user",
			'names': self.names,
			'phone': self.phone,
			'email': self.email,
			'gender': self.gender,
			'age': self.age,
			'celo_address': f'0x{address["address"]}',
		}


class UserRole(db.Model):
	__tablename__ = 'user_roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20))
	user_role = db.relationship('User', cascade="all,delete", backref='role', lazy=True)


class Invoice(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.ForeignKey('user.id'), nullable=False)
	merchant_request_id = db.Column(db.String(100), nullable=False)
	campaign_id = db.Column(db.ForeignKey('campaign.id'), nullable=False)
	amount = db.Column(db.Float, nullable=False)

	def __init__(self,user_id, merchant_request_id, campaign_id, amount):
		self.user_id = user_id
		self.merchant_request_id = merchant_request_id
		self.campaign_id = campaign_id
		self.amount = amount

	def save(invoice):
		db.session.add(invoice)
		try:
			db.session.commit()
			return {"status": True}
		except Exception as e:
			return {"status": False, "message": str(e)}

class Campaign(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='cascade'), nullable=False)
	name = db.Column(db.String(200), nullable=False)
	description = db.Column(db.String(1000), nullable=False)
	male_demographic = db.Column(db.Boolean, nullable=False)
	female_demographic = db.Column(db.Boolean, nullable=False)
	min_targeted_ages = db.Column(db.Integer, nullable=False)
	max_targeted_ages = db.Column(db.Integer, nullable=False)
	format = db.Column(db.String(10), nullable=False)
	link = db.Column(db.String(500), nullable=False)
	status = db.Column(db.Boolean, nullable=False)
	address = db.Column(db.String(100))
	thumbnail = db.Column(db.String(500))

	def __init__(self,user_id, name, description, male_demographic, female_demographic, min_targeted_ages, max_targeted_ages, format, link, thumbnail):
		self.user_id = user_id
		self.name = name
		self.description = description
		self.male_demographic = male_demographic
		self.female_demographic = female_demographic
		self.min_targeted_ages = min_targeted_ages
		self.max_targeted_ages = max_targeted_ages
		self.format = format
		self.link = link
		self.thumbnail = thumbnail
		self.status = False

	def save(campaign):
		db.session.add(campaign)
		try:
			db.session.commit()
			return {"status": True}
		except Exception as e:
			return {"status": False, "message": str(e)}

	def serialize(self):
		return{
			"id": self.id,
			"name": self.name,
			"description": self.description,
			"male_demographic": self.male_demographic,
			"female_demographic": self.female_demographic,
			"min_targeted_ages": self.min_targeted_ages,
			"max_targeted_ages": self.max_targeted_ages,
			"format": self.format,
			"link": self.link,
			"address": self.address,
			"status": self.status,
			"thumbnail": self.thumbnail,
		}

class Transaction(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	receipt_id = db.Column(db.String(100), nullable=False)
	date_paid = db.Column(db.DateTime, nullable=False)
	amount = db.Column(db.Float, nullable=False)
	user_id = db.Column(db.ForeignKey('user.id'), nullable=False)
	merchant_request_id = db.Column(db.String(100), nullable=True)

	def __init__(self,receipt_id, date_paid, amount, user_id, merchant_request_id):
		self.receipt_id = receipt_id
		self.date_paid = date_paid
		self.amount = amount
		self.user_id = user_id
		self.merchant_request_id = merchant_request_id

	def save(transaction):
		db.session.add(transaction)
		try:
			db.session.commit()
			return {"status": True}
		except Exception as e:
			return {"status": False, "message": str(e)}


def login_required(function):
	@wraps(function)
	def wrapper(*f_args, **f_kwargs):
		if "token" in request.cookies:
			token = request.cookies.get("token") 
			decoded_token = User.decode_auth_token(token)
			if decoded_token == 0:
				return make_response(jsonify({'status': 'fail', 'code':0, 'message':'Token expired. Please sign in again.'}))
			elif decoded_token == 1:
				return make_response(jsonify({'status': 'fail', 'code':1, 'message':'Authentication failed. Sign in with different credentials.'}))
			else:
				return function(*f_args, **f_kwargs)
		else:
			return make_response(jsonify({'status': 'fail', 'message': "Not authorized"})), 403
	return wrapper


@app.route('/signup', methods=['POST'])
def signup():
	post_data = request.get_json(force=True)  
	if post_data["role"] == "brand":
		company_name = post_data["names"]
		company_location = post_data["location"]
		phone = post_data["phone"]
		email = post_data["email"]
		password = post_data["password"]
		role = post_data["role"]
		company = User(UserRole.query.filter_by(name=role).first().id, phone, email, password,company_name=company_name, location=company_location)
		created_company = company.save()
		if created_company["status"]:
			token = company.encode_auth_token({'role_id': 1, 'id': company.id})
			response = {'status': 'success', 'message':'Account created successfully', "user": company.serialize_company()}
			response = make_response(jsonify(response), 200)
			response.set_cookie("token", value=token, httponly=True, samesite="None", secure=True)  

		else:
			response = {'status': 'error', 'message':created_company["message"]}
			response = make_response(jsonify(response), 500)
	
	elif post_data["role"] == "basic":
		names = post_data["names"]
		phone = post_data["phone"]
		email = post_data["email"]
		password = post_data["password"]
		role = post_data["role"]
		role = UserRole.query.filter_by(name=role).first()
		user = User(role.id, phone, email, password,names=names, age=None, gender=None)
		created_user = user.save()
		print(created_user)
		if created_user["status"]:
			token = user.encode_auth_token({'role_id': 2, 'id': user.id})
			response = {'status': 'success', 'message':'Account created successfully', "user": user.serialize_user()}
			response = make_response(jsonify(response), 200)
			response.set_cookie("token", value=token, httponly=True, samesite="None", secure=True)  

		else:
			response = {'status': 'error', 'message':created_user["message"]}
			response = make_response(jsonify(response), 500)

	else:
		response = {'status': 'error', 'message':"Something went wrong happened"}
		response = make_response(jsonify(response), 500)

	return response


@app.route('/signin', methods=['POST'])
def admin_signin():
	post_data = request.get_json(force=True) 
	if "email" not in post_data or "password" not in post_data or post_data["email"] == "" or post_data["password"] == "": 
		response = {'status': 'fail', 'message':'Please provide all required fields.'} 
		return make_response(jsonify(response)), 403

	password = post_data['password']
	email = post_data['email']

	user = User.query.filter_by(email = email).first()

	if user:
		if user.verify_password(password):
			role = User.query.get(user.role_id)
			token = user.encode_auth_token({'role_id': role.id, 'id': user.id})
			if role.name == "brand":
				user_details = user.serialize_company()
			else:
				user_details = user.serialize_user()

			response = {'status': 'success', 'message':'User signin successful', 'user': user_details }
			response = make_response(jsonify(response), 200)
			response.set_cookie("token", value=token, httponly=True, samesite="None", secure=True)
			return response
		else:
			response = {'status': 'fail', 'message':'Email or password mismatch'}
			return make_response(jsonify(response)), 401

	else:
		response = {'status': 'fail', "message": "Account does not seem to exist"}
		return make_response(jsonify(response)), 403


@app.route('/refresh_session')
@login_required
def refresh_token():
	token = request.cookies.get("token") 
	token = User.decode_auth_token(token)
	user = User.query.get(token["id"])
	print(user)
	if not user:
		response = {'status': 'failed', 'message':'Session expired'}    
		response = make_response(jsonify(response), 403)     
		return response

	user_role = UserRole.query.get(user.role.id)
	print(user_role)
	if user and user_role.name == "brand":
		response = {'status': 'success', 'message':'Session refreshed successfully','user': user.serialize_company()}    
		response = make_response(jsonify(response), 200)    
		print("response")
		print(response)
		return response 

	if user and user_role.name == "basic":
		response = {'status': 'success', 'message':'Session refreshed successfully','user': user.serialize_user()}    
		response = make_response(jsonify(response), 200)     
		return response


@app.route('/update_user', methods=['POST'])
@login_required
def update_user():
	post_data = request.get_json(force=True)
	token = request.cookies.get("token") 
	decoded_token = User.decode_auth_token(token)
	user = User.query.get(decoded_token["id"])
	if not user:
		response = {'status': 'fail', 'message':'User not found'} 
		return make_response(jsonify(response)), 404

# names company_name phone email age gender location logo

	if "names" in post_data and post_data["names"] != user.names:
		user.names = post_data["names"]

	if "company_name" in post_data and post_data["company_name"] != user.company_name:
		user.company_name = post_data["company_name"]

	if "phone" in post_data and post_data["phone"] != user.phone:
		user.phone = post_data["phone"]
	
	if "location" in post_data and post_data["location"] != user.location:
		user.location = post_data["location"]
	
	if "logo" in post_data and post_data["logo"] != user.logo:
		user.logo = post_data["logo"]
	
	saved_user = user.save()
	if saved_user["status"]:
		serialized_data = user.serialize_company() if UserRole.query.get(user.role_id).name == "brand" else user.serialize_user()
		response = {'status': 'success', "user": serialized_data}
		return make_response(jsonify(response)), 200
	else:
		response = {'status': 'error', 'message': saved_user["message"]}
		return make_response(jsonify(response)), 500     

@app.route('/payments/mpesa', methods=['POST'])
@login_required
def mpesa_express():
	post_data = request.get_json(force=True)
	name = post_data['name']
	description = post_data['description']
	male_demographic = True if post_data['demographicMale'] == "on" else False
	female_demographic = True if post_data['demographicFemale'] == "on" else False
	min_targeted_ages = post_data['ageFrom']
	max_targeted_ages = post_data['ageTo']
	format = post_data['format']
	link = post_data['link']
	thumbnail = post_data['thumbnail']
	phone = post_data['phone']
	amount = post_data['amount']
	token = request.cookies.get("token") 
	token = User.decode_auth_token(token)
	
	campaign = Campaign(token["id"], name, description, male_demographic, female_demographic, min_targeted_ages, max_targeted_ages, format, link, thumbnail)
	saved_campaign = campaign.save()
	print(saved_campaign)
	if not saved_campaign["status"]:
		return make_response(jsonify({'status': 'fail', 'message': saved_campaign["message"]})), 500

	data = {
		"business_shortcode": "174379",
		"passcode": "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919",
		"amount": "1", 
		"phone_number":f"{phone}",
		"reference_code": "XAUDIFOMII",
		"callback_url": "https://ee41-41-212-40-82.ngrok.io/payments/mpesa/callback-url", 
		"description": f"Payment for marketing campaign on Cedo" 
	}
	resp = mpesa_api.MpesaExpress.stk_push(**data)  
	invoice = Invoice(token["id"], resp['MerchantRequestID'], campaign.id, amount)
	saved_invoice = invoice.save()
	if saved_invoice["status"]:
		return make_response(jsonify({'status': 'success', 'merchantRequestId': resp['MerchantRequestID']})), 200
	else:
		return make_response(jsonify({'status': 'fail', 'message': saved_invoice["message"]})), 500

   
@app.route('/payments/mpesa/callback-url',methods=["POST"])
def airtime_callbackurl():
	post_data = request.get_json(force=True)
	invoice = Invoice.query.filter_by(merchant_request_id = post_data["Body"]["stkCallback"]["MerchantRequestID"]).first()
	result_code=post_data["Body"]["stkCallback"]["ResultCode"]
	print(post_data)
	if result_code != 0:
		return False

	mpesa_receipt = post_data["Body"]["stkCallback"]["CallbackMetadata"]["Item"][1]["Value"]
	date_paid = datetime.now()
	amount = invoice.amount      
	campaign_id = invoice.campaign_id
	user_id = invoice.user_id

	account = create_account("123@Iiht", amount)
	print("Accc issssssssssssssssss")
	print(account)
	campaign = Campaign.query.get(campaign_id)
	campaign.status = True
	campaign.address = json.dumps(account)
	campaign.save()

	transaction = Transaction(mpesa_receipt, date_paid, amount,user_id, invoice.merchant_request_id)
	recorded_transaction = transaction.save()

	if recorded_transaction["status"]:
		return True

@app.route('/payments/mpesa/verify', methods=["POST"])
@login_required
def verify_mpesa():
	data = request.get_json(force=True)
	print("--------Data--------")
	print(data)
	if 'merchantRequestId' not in data:
		return make_response(jsonify({'status': 'error', 'message': "No invoice found"})), 404

	merchant_request_id = data['merchantRequestId']
	transaction = Transaction.query.filter_by(merchant_request_id = merchant_request_id).first()
	
	if not transaction:
		return make_response(jsonify({'status': 'error', 'message': "No invoice found"})), 404

	return make_response(jsonify({'status': 'success'})), 200


@app.route('/get_campaigns', methods=['GET'])
@login_required
def get_campaigns():
	token = request.cookies.get("token") 
	token = User.decode_auth_token(token)
	user_campaigns = Campaign.query.filter_by(user_id = token["id"]).all()
	print(user_campaigns)
	serialized_campaigns = [campaign.serialize() for campaign in user_campaigns]
	return make_response(jsonify({'status': 'success', "campaigns": serialized_campaigns})), 200


@app.route('/get_all_campaigns', methods=['GET'])
@login_required
def get_all_campaigns():
	print("Request from app")
	campaigns = Campaign.query.filter_by(status = True).all()
	print(campaigns)
	serialized_campaigns = [campaign.serialize() for campaign in campaigns]
	return make_response(jsonify({'status': 'success', "campaigns": serialized_campaigns})), 200


@app.route('/complete_campaign', methods=['POST'])
@login_required
def complete_campaign():
	data = request.get_json(force=True)
	token = request.cookies.get("token") 
	token = User.decode_auth_token(token)
	user = User.query.get(token["id"])
	user_address = json.loads(user.celo_address)
	campaign_id = data['id']
	campaign = Campaign.query.get(campaign_id)
	campaign_address = json.loads(campaign.address)
	print("campaign_address", campaign_address)
	participated = confirm_participation(f'0x{user_address["address"]}', f'0x{campaign_address["address"]}')
	print("-------PART---------")
	print(participated)
	if participated:
		return make_response(jsonify({'status': 'success', "message": "Already participated in this campaign"})), 204
		
	payout = campaign_payout(campaign_address, "123@Iiht", f'0x{user_address["address"]}', 100)
	if payout:
		return make_response(jsonify({'status': 'success', "message": "User paid for interacting with brand"})), 200

	return make_response(jsonify({'status': 'fail', "campaigns": "Something went wrong"})), 500


@app.route('/get_accounts_txs', methods=['GET'])
@login_required
def get_transactions():
	token = request.cookies.get("token") 
	token = User.decode_auth_token(token)
	user = User.query.get(token["id"])
	user_address = json.loads(user.celo_address)
	txs = get_accounts_txs(f'0x{user_address["address"]}')
	if txs["status"] and len(txs["result"]) > 0:
		txs = [{"id": i, "symbol": txn["tokenSymbol"], "value": txn["value"]} for i, txn in enumerate(txs["result"])]
	else:
		txs = []
	balance = get_balance(user_address["address"])
	print(balance)
	return make_response(jsonify({'status': 'success', "txs": txs, "balance": balance})), 200 

if __name__ == '__main__':
	app.run()