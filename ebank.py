from flask import Flask, url_for, request, render_template, redirect, session
from pymongo import MongoClient
from bson import ObjectId
import hashlib
import time
import random


app = Flask(__name__)

app.config['SECRET_KEY'] = 'fewftgewrdsqagt5m'

client = MongoClient(
    "mongodb://sara:sara@cluster0-shard-00-00-errub.mongodb.net:27017,"
    "cluster0-shard-00-01-errub.mongodb.net:27017,cluster0-shard-00-02-errub.mongodb.net"
    ":27017/<dbname>?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")

db = client.get_database("db_ebank")
col_users = db["col_users"]


@app.route('/register', methods = ["POST", "GET"])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if col_users.find_one({"username": request.form['username']}) is not None: 
        return "Sorry, that username already exists."
    if col_users.find_one({"email": request.form["email"]}) is not None: 
        return "That email is alredy in use."

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    conf_pass = request.form["conf_pass"]
    if password != conf_pass:
        return "Passwords do not match. Try again."
    hash_object = hashlib.sha512(password.encode())
    password_hashed = hash_object.hexdigest()
    
    acc_number =  random.randint(100000000000000000,999999999999999999)
    
    if col_users.find_one({"acc_number" : acc_number}) is not None:
        acc_number =  random.randint(100000000000000000,999999999999999999)

    user = {
        "username": username,
        "email": email,
        "password": password_hashed,
        "role": "user",
        "created": time.strftime("%d-%m-%Y.%H:%M:%S"),
        "balance": 0,
        "acc_number": acc_number
    }

    col_users.insert_one(user)

    return redirect(url_for("login"))


@app.route('/login', methods = ["POST", "GET"])
def login():
    if '_id' in session and session["_id"] is not None:
        return "You are already login"
    if request.method == 'GET':
        return render_template('login.html')
    else:
        hash_object = hashlib.sha512(request.form["password"].encode())
        password_hashed = hash_object.hexdigest()
        user = col_users.find_one({"username": request.form['username'], "password": password_hashed})
        if user is None: 
            return "Wrong username or password"
        session['_id'] = str(user['_id'])
        session['type'] = user['role']
        return redirect(url_for('index'))
      
@app.route('/logout')
def logout():
    if "_id" in session:
        session.pop('_id', None)
        session.pop('type', None)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/index')
def index():
    user_type = None
    if 'type' in session:
        user_type = session['type']
    return render_template('index.html', role=user_type)

@app.route('/send_money', methods = ["POST", "GET"])
def send_money():
    user_type = None
    if 'type' in session:
        user_type = session['type']
     
    if request.method == "GET":
        return render_template('send_money.html', role=user_type)  

    user_id = ObjectId(session['_id'])

    from_who = col_users.find_one({'_id': user_id})
    if from_who is None:
        return 'Error'

    amount = float(request.form['amount'])

    from_balance = from_who['balance']

    if from_balance < amount:
        return 'There is not enough money'
    
    acc_number_to = int(request.form['acc_number'])
    to_who = col_users.find_one({'acc_number': acc_number_to})

    if to_who is None:
        return 'That account number do not belong to anyone'
    if amount > 0 :
        new_balance_to = to_who['balance'] + amount
        add_amount = {"$set": {
            "balance": new_balance_to
        }}
        col_users.update_one(to_who, add_amount)

        new_balance_from = from_who['balance'] - amount
        sub_amount = {"$set":{
            "balance": new_balance_from
        }}
        col_users.update_one(from_who, sub_amount)
        return 'Money is sent'
    return 'Can not send negative sum'



@app.route('/add_money', methods = ["POST", "GET"])
def add_money():
    user_type = None
    if 'type' in session:
        user_type = session['type']
    if request.method == "GET":
        return render_template('add_money.html', role=user_type)   

    acc_number = int(request.form['acc_number'])
    amount = float(request.form['amount'])

    user = col_users.find_one({'acc_number': acc_number})
    
    if user is None:
        return 'That account number do not belong to anyone'
    if amount > 0 :
        add_amount = {"$set": {
            "balance": amount
        }}
        col_users.update_one(user, add_amount)
        return 'Money is added'
    return 'Can not add negative sum'


@app.route('/')
def hello():
    return 'ZDRAVOOO'

if __name__ == '__main__':
	app.run(debug = True)



