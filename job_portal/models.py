from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20)) 
     
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    salary = db.Column(db.String(50))
    location = db.Column(db.String(100))
    category = db.Column(db.String(100))
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
# class Job(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100))
#     description = db.Column(db.Text)
#     salary = db.Column(db.String(50))
#     location = db.Column(db.String(100))
#     category = db.Column(db.String(100))
#     company = db.Column(db.String(100))
#     employer_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# class Application(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer)
#     job_id = db.Column(db.Integer)
#     resume = db.Column(db.String(200))
#     date_applied = db.Column(db.DateTime, default=datetime.utcnow)
#     status = db.Column(db.String(20), default="Pending")
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 👈 THIS IS REQUIRED

    resume = db.Column(db.String(200))
    status = db.Column(db.String(20), default="Pending")

    job = db.relationship('Job', backref='applications')
    user = db.relationship('User', backref='applications')
   

