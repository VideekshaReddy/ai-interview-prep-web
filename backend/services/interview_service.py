
from backend.services.ai_service import generate_ai_questions


def generate_questions(
    interview_type,
    number_of_questions,
    job_role="Software Developer",
    difficulty="Beginner",
    skills=None
):
    """
    Generate interview questions using Gemini AI.
    """

    questions = generate_ai_questions(
        job_role=job_role,
        interview_type=interview_type,
        difficulty=difficulty,
        number_of_questions=number_of_questions,
        skills=skills
    )

    return questions