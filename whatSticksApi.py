from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os


from datetime import datetime, date

from flask import current_app
from flask_bcrypt import Bcrypt

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()
import json

#Init app
app=Flask(__name__)

basdir = os.path.abspath(os.path.dirname(__file__))
#database
if os.environ.get('COMPUTERNAME')=='CAPTAIN2020':
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///D:/databases/whatSticks/whatSticks.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI']="sqlite:////home/ubuntu/databases/whatSticks/whatSticks.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)
#init bcyrpt
bcrypt = Bcrypt()

# Product Class/Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    image_file = db.Column(db.Text,nullable=False, default='default.jpg')
    password = db.Column(db.Text, nullable=False)
    user_timezone = db.Column(db.Text, default='US/Eastern')
    permission = db.Column(db.Text)
    theme = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, default=datetime.now)
    posts = db.relationship('Post', backref='author', lazy=True)
    variable = db.relationship('Health_description', backref='users_health_data', lazy=True)
    # track_inv = db.relationship('Tracking_inv', backref='updator_inv', lazy=True)

    def __init__(self, username, email, image_file, password):
        self.username = username
        self.email = email
        self.image_file = image_file
        self.password = password
    
    def __repr__(self):
        return f"User('{self.id}', email:'{self.email}', permission:'{self.permission}', user_timezone: '{self.user_timezone}')"

#taken from grinberg but adjusted to use bcrypt
    def hash_password(self, password_uncrypted):
        self.password = bcrypt.generate_password_hash(password_uncrypted).decode('utf-8')

    def verify_password(self, password_try):
        return bcrypt.check_password_hash(self.password, password_try)



class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content = db.Column(db.Text)
    screenshot = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}')"


class Health_description(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime_of_activity=db.Column(db.DateTime)
    var_activity = db.Column(db.Text) #walking, running, empty is ok for something like mood
    var_type = db.Column(db.Text) #heart rate, mood, weight, etc.
    var_periodicity = db.Column(db.Text)
    var_timezone_utc_delta_in_mins = db.Column(db.Float) #difference bewteen utc and timezone of exercise
    time_stamp_utc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source_filename =db.Column(db.Text)
    metric1_carido=db.Column(db.Float)
    metric2_session_duration=db.Column(db.Float)
    metric3=db.Column(db.Float)
    metric4=db.Column(db.Float)
    metric5=db.Column(db.Float)
    note=db.Column(db.Text)

    def __init__(self, datetime_of_activity, var_activity, var_type,
        var_timezone_utc_delta_in_mins,time_stamp_utc, user_id, source_filename,
        note):
        self.datetime_of_activity = datetime_of_activity
        self.var_activity = var_activity
        self.var_type = var_type
        self.var_timezone_utc_delta_in_mins = var_timezone_utc_delta_in_mins
        self.time_stamp_utc = time_stamp_utc
        self.user_id = user_id
        self.source_filename = source_filename
        self.note = note


    def __repr__(self):
        return f"Health_description('{self.id}',var_activity:'{self.var_activity}'," \
        f"'var_type: {self.var_type}', datetime_of_activity: '{self.datetime_of_activity}', time_stamp_utc: '{self.time_stamp_utc}')"
    

class Health_measure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description_id=db.Column(db.Integer, db.ForeignKey('health_description.id'), nullable=False)
    var_datetime_utc = db.Column(db.DateTime, nullable=True)
    var_value = db.Column(db.Text)
    var_unit = db.Column(db.Text)
    var_type = db.Column(db.Text)
    heart_rate = db.Column(db.Integer)
    speed=db.Column(db.Float)
    distance=db.Column(db.Float)
    longitude=db.Column(db.Float)
    latitude=db.Column(db.Float)
    altitude=db.Column(db.Float)
    
    def __repr__(self):
        return f"Variables('{self.id}',description_id:'{self.description_id}'," \
        f"'var_datetime_utc: {self.var_datetime_utc}', var_value: '{self.var_value}')"

# Product Schema
class UserSchema(ma.Schema):
  class Meta:
    fields = ('id', 'username', 'email', 'image_file', 'password_hash',
        'user_timezone','permission','theme')



# Product Schema
class Health_description_Schema(ma.Schema):
  class Meta:
    fields = ('datetime_of_activity', 'var_activity', 'var_type', 
        'var_timezone_utc_delta_in_mins','time_stamp_utc','user_id', 'source_filename',
        'note')
    # fields = ('id', 'datetime_of_activity', 'var_activity', 'var_type', 'var_periodicity',
        # 'var_timezone_utc_delta_in_mins','time_stamp_utc','user_id', 'source_filename',
        # 'metric1_carido','metric2_session_duration','metric3','note')

#Init schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)

Health_description_schema=Health_description_Schema()
Health_descriptions_schema=Health_description_Schema(many=True)


@auth.verify_password
def verify_password(email, password_try):
    user = User.query.filter_by(email = email).first()
    if user.email==email and user.verify_password(password_try):
        return True
    else:
        return False


# Get All Products
@app.route('/are_we_working', methods=['GET'])
def are_we_working():
  # users = User.query.all()
  # result = users_schema.dump(users)
  string_dict={}
  string_dict['API_status']='All systems go'
  return jsonify(string_dict)




# Get All Products
@app.route('/get_users', methods=['GET'])
@auth.login_required
def get_users():
  users = User.query.all()
  result = users_schema.dump(users)
  return jsonify(result)

# Get One User
@app.route('/get_user/<id>', methods=['GET'])
@auth.login_required
def get_user(id):
  user1 = User.query.get(id)
  result = user_schema.dump(user1)
  return jsonify(result)


@app.route('/add_user', methods=['POST'])
@auth.login_required
def add_user():
  username = request.json['username']
  email = request.json['email']
  image_file = request.json['image_file']
  password = request.json['password']
  encrypted_password=bcrypt.generate_password_hash(password).decode('utf-8')
  new_user = User(username, email, image_file, encrypted_password)

  db.session.add(new_user)
  db.session.commit()

  return user_schema.jsonify(new_user)

# Delete User
@app.route('/get_user/<id>', methods=['DELETE'])
@auth.login_required
def delete_user(id):
    user1 = User.query.get(id)
    db.session.delete(user1)
    db.session.commit()

    return user_schema.jsonify(user1)


# Get All Health_descriptions
@app.route('/get_user_health_descriptions/<user_id>', methods=['GET'])
@auth.login_required
def get_health_descriptions(user_id):
    if user_id==2:
        user_id=1
    health_descriptions = Health_description.query.filter(Health_description.user_id==user_id).all()
    result = Health_descriptions_schema.dump(health_descriptions)
    return jsonify(result)


# Get ONE Health_descriptions
@app.route('/get_health_descriptions/<description_id>', methods=['GET'])
@auth.login_required
def get_health_description(description_id):
  health_description = Health_description.query.get(description_id)
  result = Health_description_schema.dump(health_description)
  return jsonify(result)


@app.route('/add_activity', methods=['POST'])
@auth.login_required
def add_activity():   
    datetime_of_activity_str=request.json['datetime_of_activity']
    datetime_of_activity=datetime.strptime(datetime_of_activity_str, '%Y-%m-%dT%H:%M:%S')
    var_activity=request.json['var_activity']
    var_type=request.json['var_type']#Activity
    var_timezone_utc_delta_in_mins=float(request.json['var_timezone_utc_delta_in_mins'])
    time_stamp_utc_str=request.json['time_stamp_utc']
    time_stamp_utc=datetime.strptime(time_stamp_utc_str, '%Y-%m-%dT%H:%M:%S.%f')
    user_id=request.json['user_id']
    source_filename=request.json['source_filename']
    note=request.json['note']

    new_acivity=Health_description(datetime_of_activity,var_activity,var_type,
        var_timezone_utc_delta_in_mins,time_stamp_utc,user_id,
        source_filename, note)

    db.session.add(new_acivity)
    db.session.commit()

    return Health_description_schema.jsonify(new_acivity)

# Delete Activity
@app.route('/get_health_descriptions/<description_id>', methods=['DELETE'])
@auth.login_required
def delete_activity(description_id):
    health_description = health_description.query.get(description_id)
    db.session.delete(health_description)
    db.session.commit()

    return Health_description_schema.jsonify(health_description)


#Run SErver
if __name__=='__main__':
    app.run(debug=True)
    
    
    
    
    
    
    
    
    