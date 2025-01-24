import random, string, os, secrets, io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from PIL import Image
from flask import render_template, session, url_for, flash, redirect, Blueprint, jsonify, send_file
from flask_login import login_required, current_user, login_user, logout_user
from cbt_test.forms import registrationStudent, registrationExam, registrationAdmin, loginForm, singleCheck, userLoginPage, examField, downloadAllStudent
from werkzeug.security import check_password_hash, generate_password_hash
from cbt_test.models import Admin, Student, testQuestion
from cbt_test import db

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    total_admin = Admin.query.count()
    total_super_admin = Admin.query.filter(Admin.auth == 'Super Admin').count()
    total_students = Student.query.count()
    average_score = 50
    above_average_count = Student.query.filter(Student.score >= average_score).count()
    below_average_count = Student.query.filter(Student.score < average_score).count()
    total_left_student = Student.query.filter(Student.score == None).count()
    return render_template("home.html", 
                           total_students=total_students, 
                           above_average_count=above_average_count, 
                           below_average_count=below_average_count,
                           total_admin = total_admin,
                           total_super_admin = total_super_admin,
                           total_left_student = total_left_student
                           )

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = loginForm()
    if form.validate_on_submit():
        user_input = form.username.data.strip().lower() 
        user = Admin.query.filter_by(username=user_input).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)
            return redirect(url_for('main.home'))
        else:
            flash('Email or Password incorrect', 'heading')

    return render_template("login.html", form=form)

@main.route("/manage_student", methods=['GET', 'POST'])
@login_required
def manageStudent():
    form = registrationStudent()
    if form.submit.data:
        if form.fullname.data == '' or form.email.data == '':
            flash('All field is required', 'heading')
        else:
            try:
                user_input = form.studentID.data.strip().lower()
                student = Student(studentID=user_input, fullname=form.fullname.data, email=form.email.data)
                db.session.add(student)
                db.session.commit()
                flash('Student has been registered!', 'success')
                form.studentID.data = ''
                form.fullname.data = ''
                form.email.data = ''
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding question: {str(e)}', 'danger')
                return redirect(url_for('main.manageStudent'))
    elif form.search.data: 
        user_input = form.studentID.data.strip().lower()
        student = Student.query.filter_by(studentID=user_input).first()
        if student:
            form.fullname.data = student.fullname
            form.email.data = student.email
        else:
            flash('Invalid Student ID!', 'heading')
    elif form.update.data:
        user_input = form.studentID.data.strip().lower()
        student = Student.query.filter_by(studentID=user_input).first()
        if student:
            try:
                student.fullname = form.fullname.data
                student.email = form.email.data
                db.session.commit()
                flash('Student has been updated successfully!', 'success')
                form.studentID.data = ''
                form.fullname.data = ''
                form.email.data = ''
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding question: {str(e)}', 'danger')
                return redirect(url_for('main.manageStudent'))
        else:
            flash('Invalid Student ID!', 'heading')
    elif form.delete.data:
        adminform = current_user.username
        username = Admin.query.filter_by(username=adminform).first()
        if username and username.auth == 'Super Admin':
            user_input = form.studentID.data.strip().lower()
            student_to_delete = Student.query.filter_by(studentID=user_input).first()
            if student_to_delete:
                db.session.delete(student_to_delete)
                db.session.commit()
                flash('Student has been deleted successfully!', 'success')
                form.studentID.data = ''
                form.fullname.data = ''
                form.email.data = ''
            else:
                flash('Invalid Student ID!', 'heading')
        else:
            flash('You do not have permission to delete student details.', 'heading')

    return render_template("manage_student.html", form=form)

def savePicture(formPicture):
    if not formPicture or '.' not in formPicture.filename:
        flash("Invalid file. Please upload a valid image.", "danger")
        return None
    
    randomHex = secrets.token_hex(8)
    _, fExt = os.path.splitext(formPicture.filename)
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
    
    if fExt.lower() not in allowed_extensions:
        flash("Unsupported file extension. Please upload a valid image file.", "danger")
        return None

    pictureFilename = randomHex + fExt
    picturePath = os.path.join(main.root_path, 'static/exam_picture', pictureFilename)

    os.makedirs(os.path.dirname(picturePath), exist_ok=True)
    try:
        outPutSize = (250, 250)
        imageAfter = Image.open(formPicture)
        imageAfter.verify() 
        imageAfter = Image.open(formPicture) 
        imageAfter.thumbnail(outPutSize)
        imageAfter.save(picturePath)
    except Exception as e:
        flash(f"An error occurred while processing the image: {str(e)}", "danger")
        return None

    return pictureFilename

@main.route("/manage_exam", methods=['GET', 'POST'])
@login_required
def manageExam():
    form = registrationExam()
    if form.submit.data:
        if any(field == '' for field in [
            form.questionID.data, 
            form.questions.data, 
            form.option1.data, 
            form.option2.data, 
            form.option3.data, 
            form.option4.data, 
            form.answer.data
            ]):
            flash('All fields are required.', 'heading')
            return redirect(url_for('main.manageExam'))
        imageFilename = None
        if form.imageFile.data:
            imageFilename = savePicture(form.imageFile.data) 
            if not imageFilename:
                return redirect(url_for('main.manageExam'))
        try:
            test_question = testQuestion(
                questionID=form.questionID.data,
                questions=form.questions.data,
                imageFile=imageFilename,
                option1=form.option1.data,
                option2=form.option2.data,
                option3=form.option3.data,
                option4=form.option4.data,
                answer=form.answer.data
            )
            db.session.add(test_question)
            db.session.commit()
            flash('CBT test question added!', 'success')
            return redirect(url_for('main.manageExam'))  
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding question: {str(e)}', 'danger')
            return redirect(url_for('main.manageExam'))
    elif form.search.data:
        if form.questionID.data == '':
            letter = 'ESEF/PY'
            number = ''.join(random.choices(string.digits, k=3))
            random_id = letter + '/' + number
            form.questionID.data = random_id
        else:
            question = testQuestion.query.filter_by(questionID=form.questionID.data).first()
            if question:
                form.questionID.data = question.questionID
                form.questions.data = question.questions
                form.option1.data = question.option1
                form.option2.data = question.option2
                form.option3.data = question.option3
                form.option4.data = question.option4
                form.answer.data = question.answer
            else:
                flash('Invalid Question ID!', 'heading')
    elif form.update.data:
        question = testQuestion.query.filter_by(questionID = form.questionID.data).first()
        if question:
            imageFilename = None
            if form.imageFile.data:
                imageFilename = savePicture(form.imageFile.data) 
                if not imageFilename:
                    return redirect(url_for('main.manageExam'))
            try:
                question.questions = form.questions.data
                question.imageFile=imageFilename  
                question.option1 = form.option1.data
                question.option2 = form.option2.data
                question.option3 = form.option3.data
                question.option4 = form.option4.data
                question.answer = form.answer.data

                db.session.commit()
                flash('Question has been updated successfully!', 'success')
                return redirect(url_for('main.manageExam'))  
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding question: {str(e)}', 'danger')
                return redirect(url_for('main.manageExam'))
        else:
            flash('Question has not been updated successfully!', 'heading')
    elif form.delete.data:
        adminform = current_user.username
        username = Admin.query.filter_by(username=adminform).first()
        if username and username.auth == 'Super Admin':
            exam_to_delete = testQuestion.query.filter_by(questionID=form.questionID.data).first()
            if exam_to_delete:
                db.session.delete(exam_to_delete)
                db.session.commit()
                flash('Question has been deleted successfully!', 'success')
                return redirect(url_for('main.manageExam')) 
            else:
                flash('Invalid Student ID!', 'heading')
        else:
            flash('You do not have permission to delete student details.', 'heading')

    return render_template("manage_exam.html", form=form)

@main.route("/add_admin", methods=['GET', 'POST'])
@login_required
def addAdmin():
    form = registrationAdmin()
    if current_user.auth != 'Super Admin':
        flash('You do not have permission to add another admin.', 'heading')
        return redirect(url_for('main.home'))

    if form.validate_on_submit():
        user_input = form.username.data.strip().lower()
        existing_user = Admin.query.filter(
            (Admin.username == user_input) | (Admin.email == form.email.data)
        ).first()
        if existing_user:
            flash('Username or Email already exists.', 'heading')
        else:
            hashed_password = generate_password_hash(form.password.data)
            admin = Admin(
                username=user_input,
                email=form.email.data,
                password=hashed_password,
                auth=form.auth.data if current_user.auth == 'Super Admin' else None
            )
            db.session.add(admin)
            db.session.commit()
            flash('Admin has been successfully registered!', 'success')
            return redirect(url_for('main.addAdmin'))
    elif form.errors:
        for field, error_messages in form.errors.items():
            for error in error_messages:
                flash(f"{field}: {error}", 'handing')

    return render_template("add_admin.html", form=form)

@main.route("/single_student", methods=['GET', 'POST'])
@login_required
def singleStudent():
    form = singleCheck()
    adminform = current_user.username
    username = Admin.query.filter_by(username=adminform).first()
    if username and username.auth == 'Super Admin':
        user = 'go'
    else:
        user = None
    if form.submit.data:
        if form.studentID.data == '':
            flash('Student ID can not be empty!', 'heading')
        else:
            user_input = form.studentID.data.strip().lower()
            student = Student.query.filter_by(studentID=user_input).first()
            if student:
                check=student.score
                if check == None:
                    form.score.data = student.status
                else:
                    form.score.data = student.score
            else:
                flash('Invalid Student ID!', 'heading')
    elif form.updateScore.data:
        user_input = form.studentID.data.strip().lower()
        student = Student.query.filter_by(studentID=user_input).first()
        if student:
            try:
                student.score = form.score.data
                student.status = 'Exam Taken'
                db.session.commit()
                flash('Student has been updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding question: {str(e)}', 'danger')
                return redirect(url_for('main.manageStudent'))
        else:
            flash('Invalid Student ID!', 'heading')
    return render_template("single_student.html", form=form, username=user)


@main.route("/all_student", methods=['GET', 'POST'])
@login_required
def allStudent():
    students=Student.query.all()
    form = downloadAllStudent()

    if form.downloadAllStudent.data:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer)

        data = [["Student ID", "Fullname", "Email", "Score"]]

        styles = getSampleStyleSheet()
        title = Paragraph("Student Full Details", styles['Title'])

        y = 760 
        for student in students:
            data.append([
                student.studentID,
                student.fullname,
                student.email,
                student.score if student.score is not None else student.status,
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), 
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), 
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black) 
        ]))

        elements = [title, Spacer(1, 20), table]
        doc.build(elements)
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, as_attachment=True, download_name="students_table.pdf", mimetype='application/pdf')
    
    elif form.downloadScoreStudent.data:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer)

        data = [["Student ID", "Fullname", "Email", "Score"]]

        styles = getSampleStyleSheet()
        title = Paragraph("Student Full Details", styles['Title'])

        y = 760 
        for student in students:
            if student.score is not None:
                data.append([
                    student.studentID,
                    student.fullname,
                    student.email,
                    student.score if student.score is not None else student.status,
                ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), 
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), 
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black) 
        ]))

        elements = [title, Spacer(1, 20), table]
        doc.build(elements)
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, as_attachment=True, download_name="students_table.pdf", mimetype='application/pdf')
    
    elif form.downloadNoScoreStudent.data:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer)

        data = [["Student ID", "Fullname", "Email", "Score"]]

        styles = getSampleStyleSheet()
        title = Paragraph("Student Full Details", styles['Title'])

        y = 760 
        for student in students:
            if student.score is None:
                data.append([
                    student.studentID,
                    student.fullname,
                    student.email,
                    student.score if student.score is not None else student.status,
                ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), 
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), 
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black) 
        ]))

        elements = [title, Spacer(1, 20), table]
        doc.build(elements)
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, as_attachment=True, download_name="students_table.pdf", mimetype='application/pdf')

    return render_template("all_student.html",  form=form, students=students)

@main.route("/logout")
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('main.login'))

@main.route("/all_question", methods=['GET', 'POST'])
@login_required
def allQuestion():
    questions=testQuestion.query.all()
    for question in questions:
        if question.imageFile:
            question.imageFileUrl = url_for('static', filename='exam_picture/' + question.imageFile)
        else:
            question.imageFileUrl = None

    return render_template("all_question.html", questions=questions)

@main.route("/user_login", methods=['GET', 'POST'])
def userLogin():    
    form = userLoginPage()
    if form.validate_on_submit():
        user_input = form.studentID.data.strip().lower()
        user = Student.query.filter_by(studentID=user_input).first()
        if user:
            session['studentID'] = user.studentID
            session['fullname'] = user.fullname
            session['logged_in'] = True  
            return redirect(url_for('main.userHome'))
        else:
            flash('Incorrect Student ID! Please check or contact Admin', 'heading')

    return render_template("user_login.html", form=form)

@main.route("/user_home", methods=['GET', 'POST'])
def userHome():
    student = Student.query.filter_by(studentID=session['studentID']).first()
    score = Student.query.filter_by(studentID=session.get('studentID')).first()
    return render_template("user_home.html", score=score, student=student)

@main.route("/exam_section", methods=['GET', 'POST'])
def examSection():
    form = examField()
    questions = testQuestion.query.all()
    total_questions = len(questions)

    if 'exam_started' not in session:
        session.update({
            'exam_started': False,
            'user_answers': [""] * total_questions,
            'score': 0,
            'correct_answers': [False] * total_questions,
            'exam_time_left': 60 * 20
        })

    current_question = session.get('current_question', 0)
    exam_started = session.get('exam_started', False)
    user_answers = session.get('user_answers', [""] * total_questions)
    scores = session.get('score', 0)
    correct_answers = session.get('correct_answers', [False] * total_questions)
    exam_time_left = session.get('exam_time_left', 0)
    imageFile, question = None, None

    if 'studentID' in session:
        student = Student.query.filter_by(studentID=session['studentID']).first()
        if student and student.status == "Exam Taken":
            flash('You already taken the exam', 'heading')
            return redirect(url_for('main.userHome'))
    else:
        flash('Please login again', 'heading')
        return redirect(url_for('main.userLogin'))

    if exam_started and questions:
        question = questions[current_question]
        options = [question.option1, question.option2, question.option3, question.option4]
        form.formOptions.choices = [(option, option) for option in options if option]
        imageFile = question.imageFile if question.imageFile else None

    if form.startExam.data:
        session.update({
            'exam_started': True,
            'current_question': 0,
            'user_answers': [""] * total_questions,
            'score': 0,
            'correct_answers': [False] * total_questions,
            'exam_time_left': 60 * 20
        })
        return redirect(url_for('main.examSection'))

    if form.nextExam.data and exam_started:
        selected_answer = form.formOptions.data
        if selected_answer:
            was_correct = correct_answers[current_question]
            is_now_correct = selected_answer == question.answer

            if not was_correct and is_now_correct:
                session['score'] += 10  
            elif was_correct and not is_now_correct:
                session['score'] -= 10 

            user_answers[current_question] = selected_answer
            session['user_answers'] = user_answers
            correct_answers[current_question] = is_now_correct
            session['correct_answers'] = correct_answers

        if current_question + 1 < total_questions:
            session['current_question'] += 1
        return redirect(url_for('main.examSection'))

    if form.previousExam.data and exam_started:
        selected_answer = form.formOptions.data
        if selected_answer:
            was_correct = correct_answers[current_question]
            is_now_correct = selected_answer == question.answer

            if not was_correct and is_now_correct:
                session['score'] += 10  
            elif was_correct and not is_now_correct:
                session['score'] -= 10  

            user_answers[current_question] = selected_answer
            session['user_answers'] = user_answers
            correct_answers[current_question] = is_now_correct
            session['correct_answers'] = correct_answers

        if current_question > 0:
            session['current_question'] -= 1
        return redirect(url_for('main.examSection'))

    if form.endExam.data and exam_started:
        selected_answer = form.formOptions.data
        if selected_answer:
            was_correct = correct_answers[current_question]
            is_now_correct = selected_answer == question.answer

            if not was_correct and is_now_correct:
                session['score'] += 10  
            elif was_correct and not is_now_correct:
                session['score'] -= 10  

            user_answers[current_question] = selected_answer
            session['user_answers'] = user_answers
            correct_answers[current_question] = is_now_correct
            session['correct_answers'] = correct_answers
        print(session)

        if 'studentID' in session:
            print('abour to save')
            student = Student.query.filter_by(studentID=session['studentID']).first()
            print(student)
            if student:
                student.score = session.get('score', 0)
                student.status = "Exam Taken"
                db.session.commit()

        session_keys = ['current_question', 'exam_started', 'user_answers', 'score', 'correct_answers', 'exam_time_left']
        for key in session_keys:
            session.pop(key, None)

        return redirect(url_for('main.examComplete'))

    return render_template(
        'exam_section.html',
        form=form,
        current_question=current_question if exam_started else None,
        form_options=zip(form.formOptions, [option[1] for option in form.formOptions.choices]) if exam_started else [],
        total_questions=total_questions,
        question=question if exam_started else None,
        exam_started=exam_started,
        user_answer=user_answers[current_question] if exam_started else None,
        scores=scores,
        imageFile=imageFile,
        show_previous=current_question > 0,
        show_next=current_question < total_questions - 1,
        end_exam_button=current_question == total_questions - 1,
        exam_time_left=exam_time_left  
    )

@main.route('/end_exam', methods=['POST'])
def end_exam():
    if 'exam_started' in session and session['exam_started']:
        session['exam_started'] = False

        if 'studentID' in session:
            student = Student.query.filter_by(studentID=session['studentID']).first()
            if student:
                student.score = session.get('score', 0)
                student.status = "Exam Taken"
                db.session.commit()

        session_keys = ['current_question', 'exam_started', 'user_answers', 'score', 'correct_answers', 'exam_time_left']
        for key in session_keys:
            session.pop(key, None)

    return jsonify({'success': True})

@main.route('/update_timer', methods=['POST'])
def update_timer():
    if 'exam_started' in session and session['exam_started']:
        if session['exam_time_left'] > 0:
            session['exam_time_left'] -= 1
        else:
            return jsonify({'time_left': 0, 'time_up': True})
    return jsonify({'time_left': session.get('exam_time_left', 0), 'time_up': False})


@main.route("/exam_complete", methods=['GET', 'POST'])
def examComplete():
    score = Student.query.filter_by(studentID=session.get('studentID')).first()
    return render_template('user_home.html', score=score)

@main.route("/user_logout")
def userLogout():
    session.clear()
    return redirect(url_for('main.userLogin'))