from flask import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy

from flask_marshmallow import Marshmallow # importing Marshmallow for easy object serialization
from marshmallow import Schema, post_dump

import sqlalchemy
from sqlalchemy import exc # importing exc for error handling on the create_customer endpoint

import datetime
import uuid

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
ma = Marshmallow(app)

class Customer(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	full_name = db.Column(db.String(256))
	created = db.Column(db.Date)
	password = db.Column(db.String(256))
	fb_id = db.Column(db.Integer)
	google_id = db.Column(db.Integer)
	stripe_token = db.Column(db.String(256))
	email = db.Column(db.String(80), unique=True)
	phone_number = db.Column(db.String(256))
	country_of_residence = db.Column(db.String(10))
	timezone = db.Column(db.String(20))
	gender = db.Column(db.String(1))
	birthday = db.Column(db.String(20))

# Create BaseSchema that does not print null values
class BaseSchema(Schema): 
    SKIP_VALUES = set([None])

    @post_dump
    def remove_skip_values(self, data):
        return {
            key: value for key, value in data.items()
            if value not in self.SKIP_VALUES
        }

# Create CustomerSchema that defines the fields we want to see on return
class CustomerSchema(BaseSchema):
	class Meta:
		fields = (	'id',
					'full_name',
					'created',
					'fb_id',
					'google_id',
					'stripe_token',
					'email',
					'phone_number',
					'country_of_residence',
					'timezone',
					'gender',
					'birthday'
				)

customer_schema=CustomerSchema()
customers_schema=CustomerSchema(many=True)

# Returns a list of all the customers
@app.route('/customers/', methods = ['GET'])
def index():
	customers = Customer.query.all()
	result = customers_schema.dump(customers)
	return jsonify(result.data)

# Returns a specific customer if found by an id, otherwise an error
@app.route('/customers/<int:id>', methods = ['GET'])
def get_customer(id):
	customer = Customer.query.get(id)
	result = customer_schema.dump(customer)
	if result.data:
		return jsonify(result.data), 200
	else:
		return jsonify({'error' : 'user not found'}), 404

# Creates a new customer if constraints are satifsfied, otherwise throws and error
@app.route('/customers/', methods = ['POST'])
def create_customer():
	request_json = request.json

	if not request_json:
		return jsonify({'error' : 'bad request. please use JSON format'}), 400

	email 					= request_json.get('email')
	full_name 				= request_json.get('full_name')
	password 				= request_json.get('password') # should hash the user password here for security
	fb_id 					= request_json.get('fb_id')
	google_id 				= request_json.get('google_id')
	stripe_token 			= uuid.uuid4().hex # for simplicity, i generate a random hash here. normally the stripe library and a license would be necessary to generate a valid token
	phone_number 			= request_json.get('phone_number')
	country_of_residence 	= request_json.get('country_of_residence')
	timezone 				= request_json.get('timezone')
	gender 					= request_json.get('gender')
	birthday 				= request_json.get('birthday')

	new_customer = Customer(
		full_name=full_name,
		created=datetime.datetime.now(),
		password=password,
		fb_id=fb_id,
		google_id=google_id,
		stripe_token=stripe_token,
		email=email,
		phone_number=phone_number,
		country_of_residence=country_of_residence,
		timezone=timezone,
		gender=gender,
		birthday=birthday
		)

	try:
		db.session.add(new_customer)
		db.session.commit()
	except sqlalchemy.exc.IntegrityError:
		return jsonify({'error' : 'email address is in use'}), 400

	result=customer_schema.dump(new_customer)

	return jsonify(result), 201

# Updates a Customer with new information
@app.route('/customers/<int:id>', methods = ['PUT'])
def update_customer(id):
	request_json = request.json

	if not request_json:
		return jsonify({'error' : 'bad request. please use JSON format'}), 400

	# extra error handling can be added here on an individual field level
	# email validation, password strength, etc.

	customer = Customer.query.get(id)

	customer.email 					= request_json.get('email', customer.email)
	customer.full_name 				= request_json.get('full_name', customer.full_name)
	customer.password 				= request_json.get('password', customer.password)
	customer.fb_id 					= request_json.get('fb_id', customer.fb_id)
	customer.google_id 				= request_json.get('google_id', customer.google_id)
	customer.phone_number 			= request_json.get('phone_number', customer.phone_number)
	customer.country_of_residence 	= request_json.get('country_of_residence', customer.country_of_residence)
	customer.timezone 				= request_json.get('timezone', customer.timezone)
	customer.gender 				= request_json.get('gender', customer.gender)
	customer.birthday 				= request_json.get('birthday', customer.birthday)

	try:
		db.session.commit()
	except sqlalchemy.exc.IntegrityError:
		return jsonify({'error' : 'email address is in use'}), 400

	result=customer_schema.dump(customer)
	return jsonify(result), 200

if __name__ == '__main__':
    app.run()