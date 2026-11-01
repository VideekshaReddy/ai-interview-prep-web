import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load .env file
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# Read Groq API key
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("Groq API key not found!")

# Initialize Groq
client = Groq(api_key=API_KEY)

# Groq model
MODEL_NAME = "openai/gpt-oss-120b"


def test_groq_connection():
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": "Introduce yourself as the PrepAI assistant."
            }
        ]
    )

    return response.choices[0].message.content


def generate_ai_questions(
    job_role,
    interview_type,
    difficulty,
    number_of_questions,
    skills=None
):
    skills = skills or []

    prompt = f"""
    You are an expert technical and HR interview question generator
    for a placement preparation platform called PrepAI.

    Generate exactly {number_of_questions} interview questions.

    Job role: {job_role}
    Interview type: {interview_type}
    Difficulty: {difficulty}
    Candidate skills: {", ".join(skills) if skills else "Not specified"}

    Instructions:
    1. Generate relevant and realistic interview questions.
    2. Match the selected difficulty level.
    3. For Technical interviews, focus on technical concepts.
    4. For HR interviews, focus on behavioral and personality questions.
    5. For Mixed interviews, include both technical and HR questions.
    6. Avoid duplicate questions.
    7. Return exactly the requested number of questions.

    Return ONLY valid JSON in this format:
    {{
        "questions": [
            "Question 1",
            "Question 2"
        ]
    }}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You generate interview questions and return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.7
    )

    response_text = response.choices[0].message.content

    result = json.loads(response_text)
    questions = result.get("questions", [])

    if (
        not isinstance(questions, list)
        or len(questions) != number_of_questions
        or not all(isinstance(q, str) and q.strip() for q in questions)
    ):
        raise ValueError("Groq returned an invalid question list.")

    return questions