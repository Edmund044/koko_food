from email import message
import datetime
from dataclasses import dataclass
from flask import Flask, render_template, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, extract, inspect
from sqlalchemy.sql import func
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS, cross_origin
# Import Module
import json
app = Flask(__name__)
CORS(app)
from random import randint

 
db =SQLAlchemy(app)
 
@dataclass
class EmployeeModel(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    employee_number = db.Column(db.String(),unique = True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String(),unique = True)
    designation = db.Column(db.String())
    department = db.Column(db.String())
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())

    def rowsToDictionary():
         employees_dictionary = []
         for employee in EmployeeModel.query.all():
          new_employee_object = employee.__dict__
          del new_employee_object['_sa_instance_state']
          employees_dictionary.append(new_employee_object)

         return employees_dictionary

@dataclass
class AdminModel(db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String(),unique = True)
    password = db.Column(db.String())
    role = db.Column(db.String())
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())

    def rowsToDictionary():
         admins_dictionary = []
         for admin in AdminModel.query.all():
          new_admin_object = admin.__dict__
          del new_admin_object['_sa_instance_state']
          admins_dictionary.append(new_admin_object)

         return admins_dictionary
@dataclass
class MealModel(db.Model):
    __tablename__ = "meals"
    id = db.Column(db.Integer(), primary_key=True)
    meal_name = db.Column(db.Integer())
    meal_description = db.Column(db.String())
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())

    def rowsToDictionary():
         meals_dictionary = []
         for meal in MealModel.query.all():
          new_meal_object = meal.__dict__
          del new_meal_object['_sa_instance_state']
          meals_dictionary.append(new_meal_object)

         return meals_dictionary
@dataclass
class TransactionsModel(db.Model):
    __tablename__ = "meal_transactions"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer(), db.ForeignKey("employees.id"))
    meal_id = db.Column(db.Integer(), db.ForeignKey("meals.id"))
    status = db.Column(db.Boolean(), default=False)
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())

    def rowsToDictionary():
        meal_transactions_query_results = db.session.query(TransactionsModel.id,TransactionsModel.time_updated,TransactionsModel.time_created,TransactionsModel.status,MealModel.meal_name.label("meal_name"),EmployeeModel.first_name.label("first_name"),EmployeeModel.last_name.label("last_name")).\
            outerjoin(MealModel, TransactionsModel.meal_id==MealModel.id).\
            outerjoin(EmployeeModel, TransactionsModel.employee_id==EmployeeModel.id).all()
        meal_transactions = [{
            'id':meal_transaction.id,
            'employee_name':meal_transaction.first_name + ' ' + meal_transaction.last_name,
            'meal_name':meal_transaction.meal_name,
            'status':meal_transaction.status, 
            'time_created':meal_transaction.time_created,
            'time_updated': meal_transaction.time_updated,

        } for meal_transaction in meal_transactions_query_results]
        return meal_transactions

    def createInvoices():    
         invoice_created_query_results = db.session.query(TransactionsModel.meal_id,TransactionsModel.time_created,func.count(TransactionsModel.meal_id).label('served_plates'),TransactionsModel.time_created).filter(TransactionsModel.status == False).group_by(func.strftime('%m', TransactionsModel.time_created))
         invoices_created = [{
            'invoice_number': "KF{}".format(invoice_created.time_created.strftime('%Y%m%d')),
            'served_plates':invoice_created.served_plates,
            'amount_in_ksh':invoice_created.served_plates * 300,
            'date':invoice_created.time_created.strftime('%Y%m%d'),
            'status':False

        } for invoice_created in invoice_created_query_results]
         return invoices_created
        


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///koko_food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.before_first_request
def create_table():
    db.create_all()

@app.route("/")
@cross_origin()
def index():
    return render_template("index.html")

@app.route("/dashboard")
@cross_origin()
def dashboard():
    return render_template("dashboard.html")

@app.route("/admin-signup", methods=['POST'])
@cross_origin()
def signupAdmin():
        if request.method == "POST":
            body = request.get_json()
            first_name = body["first_name"]
            last_name = body["last_name"]
            email = body["email"]
            role = body["role"]
            password = body["password"]
            confirm_password = body["confirm_password"]
            if password != confirm_password:
                return make_response(json.dumps({"message":"Passwords do not match"}), 500)
            admin = AdminModel.query.filter_by(email=email).first()
            if admin:
                return make_response(json.dumps({"message":"User already exists"}), 500)
            else:
             new_admin = AdminModel(first_name=first_name, last_name=last_name, email=email, password=generate_password_hash(password, method='sha256'), role=role)
             db.session.add(new_admin)
             db.session.commit()
            return make_response(json.dumps({"message":"User created successfully"}), 200)

@app.route("/admin-login", methods=['POST'])
@cross_origin()
def loginAdmin():
        if request.method == "POST":
            body = request.get_json()
            email = body["email"]
            password = body["password"]

        try:
          admin = AdminModel.query.filter_by(email=email).first()
          if admin:
            if check_password_hash(admin.password, password):
                return make_response(json.dumps({"message":"Success"}), 200)
            else:
                  return make_response(json.dumps({"message":"Password is incorrect"}), 401)
          else:
                return make_response(json.dumps({"message":"User does not exist"}), 403)
          

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 

@app.route("/update-admin", methods=['PUT'])
@cross_origin()
def updateAdmin():
        if request.method == "PUT":
            body = request.get_json()
            admin_id = body["admin_id"]
            first_name = body["first_name"]
            last_name = body["last_name"]
            email = body["email"]
            role = body["role"]
            password = body["password"]
            confirm_password = body["confirm_password"]
            if password != confirm_password:
                return make_response(json.dumps({"message":"Passwords do not match"}), 500)
        try:
         admin = AdminModel.query.filter(AdminModel.id == admin_id).first()
         admin.first_name = first_name
         admin.last_name = last_name
         admin.email = email
         admin.role = role 
         admin.password = generate_password_hash(password, method='sha256')
         db.session.commit()   
         return make_response(json.dumps({"message":"Success"}), 200)

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 



@app.route("/create-employee", methods=['GET', 'POST'])
@cross_origin()
def createEmployee():
        if request.method == "GET":
            return render_template("index.html")

        if request.method == "POST":
            body = request.get_json()
            employee_number = body["employee_number"]
            first_name = body["first_name"]
            last_name = body["last_name"]
            email = body["email"]
            designation = body["designation"]
            department = body["department"]

        try:
         new_employee = EmployeeModel(first_name=first_name, last_name=last_name, email=email,designation=designation, department=department, employee_number=employee_number)
         db.session.add(new_employee)
         db.session.commit()
         return make_response(json.dumps({"message":"Success"}), 200)

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 

@app.route("/employee-login", methods=['POST'])
@cross_origin()
def loginEmployee():
        if request.method == "POST":
            body = request.get_json()
            email = body["email"]

        try:
          employee = EmployeeModel.query.filter_by(email=email).first()
          if employee:
                return make_response(json.dumps({"message":"Success","employee_id":employee.id}), 200)
          else:
                return make_response(json.dumps({"message":"Employee does not exist"}), 403)
          

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         print(e)
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 



@app.route("/update-employee", methods=['PUT'])
@cross_origin()
def updateEmployee():
        if request.method == "PUT":
            body = request.get_json()
            employee_id = body["employee_id"]
            first_name = body["first_name"]
            last_name = body["last_name"]
            designation = body["designation"]
            department = body["department"]
            
        try:
         employee = db.session.query(EmployeeModel).filter(EmployeeModel.id == employee_id ).first()
         employee.first_name = first_name
         employee.last_name = last_name
         employee.designation = designation
         employee.department = department  
         db.session.commit()   
         return make_response(json.dumps({"message":"Success"}), 200)

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 

@app.route("/retrieve-employees", methods=['GET'])
def retrieveEmployee():
    try: 
      return make_response(jsonify(data=EmployeeModel.rowsToDictionary()), 200)
    except Exception as e:  
      db.session.rollback()
      db.session.flush()
      return make_response(json.dumps({"message":"Unsuccessful"}), 500)   

@app.route("/create-transaction", methods=['POST'])
@cross_origin()
def createTransaction():
        if request.method == "POST":
            body = request.get_json()
            employee_id = body["employee_id"]

        try:
          transaction = TransactionsModel.query.filter(TransactionsModel.employee_id == employee_id,
            func.date(TransactionsModel.time_created) == date.today()
           ).first()
          if not transaction:
             meal_of_the_day = MealModel.query.filter(func.date(MealModel.time_created) == date.today())
             new_transaction = TransactionsModel(employee_id=employee_id, meal_id=meal_of_the_day.id)
             db.session.add(new_transaction)
             db.session.commit()
             return make_response(json.dumps({"message":"Success"}), 200)
             
            
          else:
             return make_response(json.dumps({"message":"Already taken Food"}), 401)

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         print(e) 
         return make_response(json.dumps({"message":"Unsuccessful"}), 500)       

@app.route("/retrieve-transactions", methods=['GET'])
def retrieveTransactions():
    try: 
      return make_response(jsonify(data=TransactionsModel.rowsToDictionary()), 200)
    except Exception as e:  
      print(e)
      db.session.rollback()
      db.session.flush()
      return make_response(json.dumps({"message":"Unsuccessful"}), 500)   
@app.route("/retrieve-invoices", methods=['GET'])
def retrieveInvoices():
    try: 
      return make_response(jsonify(data=TransactionsModel.createInvoices()), 200)
    except Exception as e:  
      print(e)
      db.session.rollback()
      db.session.flush()
      return make_response(json.dumps({"message":"Unsuccessful"}), 500)   

@app.route("/create-meal", methods=['POST'])
@cross_origin()
def createMeal():
        if request.method == "POST":
            body = request.get_json()
            meal_name = body["meal_name"]
            meal_description = body["meal_description"]

        try:
         new_meal = MealModel(meal_name=meal_name, meal_description=meal_description)
         db.session.add(new_meal)
         db.session.commit()
         return make_response(json.dumps({"message":"Success"}), 200)

        except Exception as e:
         db.session.rollback()
         print(e)
         db.session.flush()
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 

@app.route("/retrieve-meals", methods=['GET'])
def retrieveMeals():
    try: 
      return make_response(jsonify(data=MealModel.rowsToDictionary()), 200)
    except Exception as e:  
      db.session.rollback()
      db.session.flush()
      return make_response(json.dumps({"message":"Unsuccessful"}), 500)   
         

@app.route("/get-meal-by-id", methods=['GET'])
@cross_origin()
def getMealById():
        if request.method == "GET":
            body = request.get_json()
            meal_id = body["meal_id"]
        
             
        try:
         meal = db.session.query(MealModel).filter(MealModel.id == meal_id ).first()  
         return make_response(jsonify(meal.to_json()), 200)

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 

@app.route("/update-meal", methods=['PUT'])
@cross_origin()
def updateMeal():
        if request.method == "PUT":
            body = request.get_json()
            meal_id = body["meal_id"]
            meal_name = body["meal_name"]
            meal_description = body["meal_description"]
            
        try:
         meal = db.session.query(MealModel).filter(MealModel.id == meal_id ).first()
         meal.first_name = meal_name
         meal.last_name = meal_description
         db.session.commit()   
         return make_response(json.dumps({"message":"Success"}), 200)

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 

@app.route("/update-transaction", methods=['PUT'])
@cross_origin()
def updateTransaction():
        if request.method == "PUT":
            body = request.get_json()
            employee_number = body["employee_number"]
            first_name = body["first_name"]
            last_name = body["last_name"]
            designation = body["designation"]
            department = body["department"]
            
        try:
         employee = db.session.query(EmployeeModel).filter(EmployeeModel.employee_number == employee_number ).first()
         employee.first_name = first_name
         employee.last_name = last_name
         employee.designation = designation
         employee.department = department  
         db.session.commit()   
         return make_response(json.dumps({"message":"Success"}), 200)

        except Exception as e:
         db.session.rollback()
         db.session.flush()
         return make_response(json.dumps({"message":"Unsuccessful"}), 500) 


         

@app.route("/prediction", methods=['GET', 'POST'])
@cross_origin()
def submit():
    if request.method == "POST":
        income = int(request.form["income"])
        limit =  randint(0,20)/100 * income
        # if income > 1000 and income <= 5000:
        #     limit = 1000
        # elif income > 3000 and income <= 50000:
        #     limit = 2000  
        # else:
        #     limit = 0     
        return render_template("prediction.html", n = limit)
       
def runServer(host='0.0.0.0'):

    app.run(host)

if __name__ == "__main__":
    try:
        runServer()
    finally:
        app.run()

