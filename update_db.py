
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():

    columns = [
        column['name']
        for column in inspect(db.engine).get_columns('interview')
    ]

    if 'student_id' not in columns:

        db.session.execute(text(
            "ALTER TABLE interview ADD COLUMN student_id INTEGER"
        ))

        db.session.commit()

        print("student_id column added successfully!")

    else:
        print("student_id column already exists!")
