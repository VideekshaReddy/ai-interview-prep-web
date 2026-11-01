
from backend.extensions import db


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    extracted_text = db.Column(db.Text)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))



class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_role = db.Column(db.String(100))
    interview_type = db.Column(db.String(50))
    difficulty = db.Column(db.String(50))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))



class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.Text)
    evaluation_json = db.Column(db.Text)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))

class Result(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    score = db.Column(db.Float)

    feedback = db.Column(db.Text)

    interview_id = db.Column(
        db.Integer,
        db.ForeignKey('interview.id'),
        unique=True
    )

    interview = db.relationship(
        'Interview',
        backref=db.backref('result', uselist=False)
    )