
import os
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session, jsonify
)

from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from backend.extensions import db
from backend.services.interview_service import generate_questions
from backend.services.resume_service import (
    extract_resume_text,
    is_valid_resume,
    extract_skills,
    analyze_skill_gap
)
from backend.services.evaluation_service import evaluate_all_answers


# =====================================================
# APPLICATION CONFIGURATION
# =====================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    'FLASK_SECRET_KEY',
    'prepai-development-secret-key'
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prepai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = os.path.join(
    app.root_path, 'uploads'
)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)


# =====================================================
# DATABASE MODELS
# =====================================================

from backend.models import (
    Student,
    Resume,
    Interview,
    Question,
    Answer,
    Result
)


# =====================================================
# AI ERROR HANDLING
# =====================================================

def is_quota_error(error):

    error_message = str(error).lower()

    quota_indicators = [
        '429',
        'resource_exhausted',
        'quota exceeded',
        'rate limit',
        'requests per day limit exceeded'
    ]

    return any(
        indicator in error_message
        for indicator in quota_indicators
    )


# =====================================================
# LOGIN REQUIRED DECORATOR
# =====================================================

def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if 'student_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))

        return route_function(*args, **kwargs)

    return wrapper


# =====================================================
# HOME
# =====================================================

@app.route('/')
def home():
    return render_template('index.html')


# =====================================================
# REGISTRATION
# =====================================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('Please fill in all required fields.')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('Password must contain at least 8 characters.')
            return redirect(url_for('register'))

        existing_student = Student.query.filter_by(
            email=email
        ).first()

        if existing_student:
            flash('Email already registered.')
            return redirect(url_for('register'))

        new_student = Student(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )

        try:

            db.session.add(new_student)
            db.session.commit()

            flash('Account created successfully!')
            return redirect(url_for('login'))

        except Exception:

            db.session.rollback()
            app.logger.exception('Registration failed')

            flash('Unable to create account.')
            return redirect(url_for('register'))

    return render_template('register.html')


# =====================================================
# LOGIN
# =====================================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        student = Student.query.filter_by(
            email=email
        ).first()

        if student and check_password_hash(
            student.password_hash, password
        ):

            session.clear()

            session['student_id'] = student.id
            session['student_name'] = student.name

            flash('Login successful!')

            return redirect(url_for('dashboard'))

        flash('Invalid email or password.')
        return redirect(url_for('login'))

    return render_template('login.html')


# =====================================================
# LOGOUT
# =====================================================

@app.route('/logout')
@login_required
def logout():

    session.clear()

    flash('Logged out successfully.')

    return redirect(url_for('home'))


# =====================================================
# DASHBOARD
# =====================================================

@app.route('/dashboard')
@login_required
def dashboard():

    student_id = session['student_id']

    practice_sessions = Interview.query.filter_by(
        student_id=student_id
    ).count()

    tests_completed = Result.query.join(
        Interview
    ).filter(
        Interview.student_id == student_id
    ).count()

    average_score = db.session.query(
        db.func.avg(Result.score)
    ).join(
        Interview
    ).filter(
        Interview.student_id == student_id
    ).scalar()

    average_score = round(average_score or 0, 2)

    skills_improved = 0

    latest_report = Result.query.join(Interview).filter(
        Interview.student_id == student_id
    ).order_by(Result.id.desc()).first()

    return render_template(
        'dashboard.html',
        practice_sessions=practice_sessions,
        tests_completed=tests_completed,
        average_score=average_score,
        skills_improved=skills_improved,
        latest_report_id=(
            latest_report.interview_id if latest_report else None
        )
    )


# =====================================================
# RESUME ANALYSIS
# =====================================================

@app.route('/resume', methods=['GET', 'POST'])
@login_required
def resume():

    if request.method == 'POST':

        file = request.files.get('resume')

        if not file or not file.filename:
            flash('Please select a PDF file.')
            return redirect(url_for('resume'))

        if not file.filename.lower().endswith('.pdf'):
            flash('Only PDF files are allowed.')
            return redirect(url_for('resume'))

        filename = secure_filename(file.filename)

        if not filename:
            flash('Invalid filename.')
            return redirect(url_for('resume'))

        import uuid

        filename = f"{uuid.uuid4().hex}_{filename}"

        file_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        file.save(file_path)

        try:

            extracted_text = extract_resume_text(file_path)

            if not is_valid_resume(extracted_text):
                raise ValueError('Invalid resume document.')

            found_skills = extract_skills(extracted_text)

            target_role = request.form.get(
                'target_role', ''
            ).strip()

            if not target_role:
                raise ValueError('Please select a target role.')

            skill_analysis = analyze_skill_gap(
                found_skills,
                target_role
            )

            new_resume = Resume(
                filename=filename,
                extracted_text=extracted_text,
                student_id=session['student_id']
            )

            db.session.add(new_resume)
            db.session.commit()

            return render_template(
                'resume.html',
                found_skills=found_skills,
                required_skills=skill_analysis['required_skills'],
                matched_skills=skill_analysis['matched_skills'],
                missing_skills=skill_analysis['missing_skills'],
                target_role=target_role
            )

        except ValueError as error:

            if os.path.exists(file_path):
                os.remove(file_path)

            flash(str(error))
            return redirect(url_for('resume'))

        except Exception:

            db.session.rollback()
            app.logger.exception('Resume analysis failed')

            if os.path.exists(file_path):
                os.remove(file_path)

            flash('Unable to analyze resume.')
            return redirect(url_for('resume'))

    return render_template('resume.html')


# =====================================================
# INTERVIEW SETUP
# =====================================================

@app.route('/interview-setup')
@login_required
def interview_setup():

    return render_template('interview_setup.html')


# =====================================================
# INTERVIEW GENERATION AND DISPLAY
# =====================================================

@app.route('/interview', methods=['GET', 'POST'])
@login_required
def interview():

    if request.method == 'POST':

        role = request.form.get('role', '').strip()

        interview_type = request.form.get(
            'interview_type', ''
        ).strip()

        difficulty = request.form.get(
            'difficulty', ''
        ).strip()

        try:
            number_of_questions = int(
                request.form.get('questions', 10)
            )
        except (ValueError, TypeError):

            flash('Invalid number of questions.')
            return redirect(url_for('interview_setup'))

        if not role or not interview_type or not difficulty:
            flash('Please complete all interview selections.')
            return redirect(url_for('interview_setup'))

        if interview_type not in ['Technical', 'HR', 'Mixed']:
            flash('Invalid interview type.')
            return redirect(url_for('interview_setup'))

        if difficulty not in ['Beginner', 'Intermediate', 'Advanced']:
            flash('Invalid difficulty level.')
            return redirect(url_for('interview_setup'))

        if number_of_questions not in [5, 10, 15, 20]:
            flash('Invalid number of questions.')
            return redirect(url_for('interview_setup'))

        try:

            new_interview = Interview(
                job_role=role,
                interview_type=interview_type,
                difficulty=difficulty,
                student_id=session['student_id']
            )

            db.session.add(new_interview)
            db.session.flush()

            generated_questions = generate_questions(
                interview_type=interview_type,
                number_of_questions=number_of_questions,
                job_role=role,
                difficulty=difficulty
            )

            if (
                not generated_questions
                or len(generated_questions) != number_of_questions
            ):
                raise ValueError(
                    'Unable to generate the requested questions.'
                )

            for question_text in generated_questions:

                new_question = Question(
                    question_text=question_text,
                    interview_id=new_interview.id
                )

                db.session.add(new_question)

            db.session.commit()

            return redirect(url_for(
                'interview',
                interview_id=new_interview.id
            ))

        except Exception as error:

            db.session.rollback()

            app.logger.exception('Interview generation failed')

            if is_quota_error(error):
                flash(
                    'The AI service has reached its usage limit. '
                    'Please try again after the quota resets.'
                )
            else:
                flash(
                    'Unable to generate interview questions. '
                    'Please try again later.'
                )

            return redirect(url_for('interview_setup'))

    interview_id = request.args.get(
        'interview_id',
        type=int
    )

    if not interview_id:
        return redirect(url_for('interview_setup'))

    current_interview = Interview.query.filter_by(
        id=interview_id,
        student_id=session['student_id']
    ).first_or_404()

    saved_questions = Question.query.filter_by(
        interview_id=current_interview.id
    ).order_by(Question.id).all()

    question_list = [
        question.question_text
        for question in saved_questions
    ]

    return render_template(
        'interview.html',
        interview=current_interview,
        number_of_questions=len(question_list),
        questions=question_list
    )


# =====================================================
# FINISH INTERVIEW AND CALCULATE FINAL SCORE
# =====================================================

@app.route('/finish-interview', methods=['POST'])
@login_required
def finish_interview():

    import json

    data = request.get_json(silent=True) or {}

    try:
        interview_id = int(data.get('interview_id'))
    except (ValueError, TypeError):
        return jsonify({
            'error': 'Invalid interview selection.'
        }), 400

    submitted_answers = data.get('answers')

    if not isinstance(submitted_answers, list):
        return jsonify({
            'error': 'Invalid answers submitted.'
        }), 400

    current_interview = Interview.query.filter_by(
        id=interview_id,
        student_id=session['student_id']
    ).first()

    if not current_interview:
        return jsonify({
            'error': 'Interview not found.'
        }), 404

    questions = Question.query.filter_by(
        interview_id=interview_id
    ).order_by(Question.id).all()

    if len(submitted_answers) != len(questions):
        return jsonify({
            'error': 'Answer count does not match question count.'
        }), 400

    evaluation_items = []

    for index, question in enumerate(questions):

        answer_text = submitted_answers[index]

        if not isinstance(answer_text, str):
            return jsonify({
                'error': 'Invalid answer format.'
            }), 400

        answer_text = answer_text.strip()

        if answer_text:
            evaluation_items.append({
                'question_id': question.id,
                'question': question.question_text,
                'answer': answer_text
            })

    if not evaluation_items:
        return jsonify({
            'error': 'Please answer at least one question.'
        }), 400

    try:

        evaluations = evaluate_all_answers(
            evaluation_items,
            current_interview.job_role,
            current_interview.difficulty
        )

        if len(evaluations) != len(evaluation_items):
            raise ValueError(
                'Gemini returned an incorrect number of evaluations.'
            )

        scores = []

        for item, evaluation in zip(
            evaluation_items,
            evaluations
        ):

            score = evaluation.get('score')

            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not 0 <= score <= 10
            ):
                raise ValueError('Invalid evaluation score.')

            saved_answer = Answer.query.filter_by(
                question_id=item['question_id']
            ).first()

            if not saved_answer:
                saved_answer = Answer(
                    question_id=item['question_id']
                )
                db.session.add(saved_answer)

            saved_answer.answer_text = item['answer']

            saved_answer.evaluation_json = json.dumps(
                evaluation
            )

            scores.append(score)

        average_score = sum(scores) / len(scores)

        final_score = round(average_score * 10, 2)

        result = Result.query.filter_by(
            interview_id=interview_id
        ).first()

        if not result:
            result = Result(
                interview_id=interview_id
            )
            db.session.add(result)

        result.score = final_score

        result.feedback = (
            f'Evaluated {len(scores)} out of {len(questions)} questions. '
            f'Average score: {round(average_score, 2)}/10.'
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'score': final_score,
            'answered': len(scores),
            'total': len(questions),
            'redirect_url': url_for(
                'report',
                interview_id=interview_id
            )
        })

    except Exception as error:

        db.session.rollback()

        app.logger.exception(
            'Final interview evaluation failed'
        )

        if is_quota_error(error):
            return jsonify({
                'error': (
                    'The AI service has reached its usage limit. '
                    'Please try again after the quota resets.'
                )
            }), 429

        return jsonify({
            'error': (
                'Unable to complete interview evaluation. '
                'Please try again later.'
            )
        }), 500


# =====================================================
# INTERVIEW HISTORY
# =====================================================

@app.route('/interview-history')
@login_required
def interview_history():

    student_id = session['student_id']

    interviews = Interview.query.filter_by(
        student_id=student_id
    ).order_by(Interview.id.desc()).all()

    history = []

    for interview in interviews:

        result = Result.query.filter_by(
            interview_id=interview.id
        ).first()

        history.append({
            'id': interview.id,
            'job_role': interview.job_role,
            'interview_type': interview.interview_type,
            'difficulty': interview.difficulty,
            'score': result.score if result else None,
            'completed': result is not None
        })

    return render_template(
        'interview_history.html',
        history=history
    )


# =====================================================
# DISPLAY INTERVIEW REPORT
# =====================================================

@app.route('/report/<int:interview_id>')
@login_required
def report(interview_id):

    import json

    current_interview = Interview.query.filter_by(
        id=interview_id,
        student_id=session['student_id']
    ).first()

    if not current_interview:
        flash("Interview not found.")
        return redirect(url_for('dashboard'))

    result = Result.query.filter_by(
        interview_id=interview_id
    ).first()

    questions = Question.query.filter_by(
        interview_id=interview_id
    ).order_by(Question.id).all()

    evaluated_answers = []

    for question in questions:

        answer = Answer.query.filter_by(
            question_id=question.id
        ).first()

        if not answer or not answer.answer_text:
            continue

        evaluation = None

        if answer.evaluation_json:
            try:
                evaluation = json.loads(answer.evaluation_json)
            except (json.JSONDecodeError, TypeError):
                evaluation = None

        evaluated_answers.append({
            'question': question.question_text,
            'answer': answer.answer_text,
            'evaluation': evaluation
        })

    return render_template(
        'report.html',
        interview=current_interview,
        result=result,
        evaluated_answers=evaluated_answers,
        total_questions=len(questions),
        answered_count=len(evaluated_answers)
    )


# =====================================================
# APPLICATION START
# =====================================================

if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run(debug=True)
