from flask_wtf import FlaskForm
from flask_wtf.file import FileField, file_allowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from cbt_test.models import Student, testQuestion, Admin

class loginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class registrationStudent(FlaskForm):
    studentID = StringField('Student ID', validators=[DataRequired(), Length(min=6, max=25)])
    fullname = StringField('Fullname')
    email = StringField('Email', validators=[Email()])
    submit = SubmitField('Add Student')
    search = SubmitField('Search Student')
    update = SubmitField('Update Student')
    delete = SubmitField('Delete Student')

    def validate_username(self, studentID):
        user = Student.query.filter_by(studentID=studentID.data).first()
        if user:
            raise ValidationError('That studentID is taken, Please input a new studentID')
        
    def validate_email(self, email):
        user = Student.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken, Please choose a new email')
        
class registrationExam(FlaskForm):
    questionID = StringField('Question ID', validators=[Length(min=6, max=25)])
    questions = StringField('Question')
    imageFile = FileField('Question Image', validators=[file_allowed(['jpg', 'png', '.jpeg', '.gif'])])
    option1 = StringField('Option A')
    option2 = StringField('Option B')
    option3 = StringField('Option C')
    option4 = StringField('Option D')
    answer = StringField('Answer')
    submit = SubmitField('Add Question')
    search = SubmitField('Generate/Search Question')
    update = SubmitField('Update Question')
    delete = SubmitField('Delete Question')

    def validate_username(self, questionID):
        user = testQuestion.query.filter_by(questionID=questionID.data).first()
        if user:
            raise ValidationError('That question ID is taken, Please choose a new question ID')
        
    def validate_email(self, questions):
        user = testQuestion.query.filter_by(questions=questions.data).first()
        if user:
            raise ValidationError('That question already exist, Please choose a new question')
        
class registrationAdmin(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=6, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    auth = StringField('Authentication', default='Normal Admin')
    password = PasswordField('Password', validators=[DataRequired()])
    confirmPassword = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Add Admin')

    def validate_username(self, username):
        user = Admin.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken, Please input a new username')
        
    def validate_email(self, email):
        user = Admin.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken, Please choose a new email')
        
class singleCheck(FlaskForm):
    studentID = StringField('Student Id', validators=[DataRequired()])
    score = StringField('Student Score')
    submit = SubmitField('Check')

class userLoginPage(FlaskForm):
    studentID = StringField('Student ID', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class examField(FlaskForm):
    formOptions = RadioField(coerce=str)
    endExam = SubmitField('End Test')
    startExam = SubmitField('Start Test')
    nextExam = SubmitField('Next Question')
    previousExam = SubmitField('Previous Question')