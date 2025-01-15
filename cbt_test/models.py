from flask_login import UserMixin
from cbt_test import db, loginManager

@loginManager.user_loader
def loadUser(userID):
    return Admin.query.get(int(userID))

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    auth = db.Column(db.String(60), nullable=False, default='Normal Admin')
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"Admin('{self.username}', '{self.email}', '{self.auth}')"
    
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studentID = db.Column(db.String(25), unique=True, nullable=False)
    fullname = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(25), nullable=False, default='Text Not Taken Yet')

    def __repr__(self):
        return f"Student('{self.studentID}', {self.fullname}, '{self.email}', {self.score}, {self.status})"
    
class testQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questionID = db.Column(db.String(25), unique=True, nullable=False)
    questions = db.Column(db.String(250), unique=True, nullable=False)
    imageFile = db.Column(db.String(20), nullable=True)
    option1 = db.Column(db.String(100),  nullable=False)
    option2 = db.Column(db.String(100),  nullable=False)
    option3 = db.Column(db.String(100),  nullable=False)
    option4 = db.Column(db.String(100),  nullable=False)
    answer = db.Column(db.String(100),  nullable=False)

    def __repr__(self):
        return f"Student('{self.questionID}', '{self.questions}', {self.imageFile}, self{self.option1}, self{self.option2}, self{self.option3}, self{self.option4}, self{self.answer})"