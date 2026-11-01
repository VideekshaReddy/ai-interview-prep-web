
import fitz
import re


def extract_resume_text(file_path):
    text = ""

    pdf = fitz.open(file_path)

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text


def is_valid_resume(text):

    if not text or len(text.strip()) < 200:
        return False

    text = text.lower()

    # Common resume sections and keywords
    resume_keywords = [
        "education",
        "experience",
        "work experience",
        "skills",
        "technical skills",
        "projects",
        "internship",
        "certifications",
        "professional summary",
        "career objective",
        "achievements",
        "employment"
    ]

    # Count matching resume sections
    matches = sum(
        1 for keyword in resume_keywords
        if keyword in text
    )

    # Check for contact information
    has_email = bool(
        re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    )

    has_phone = bool(
        re.search(r'\b\d{10}\b', text)
    )

    # Require multiple resume indicators
    return matches >= 2 and (has_email or has_phone)

import re

# Skills that our system can recognize
SKILLS = [
    "Python",
    "Java",
    "C++",
    "C",
    "JavaScript",
    "HTML",
    "CSS",
    "React",
    "Flask",
    "Django",
    "SQL",
    "MySQL",
    "MongoDB",
    "PostgreSQL",
    "Data Structures",
    "Algorithms",
    "OOP",
    "DBMS",
    "Operating Systems",
    "Computer Networks",
    "Git",
    "GitHub",
    "Machine Learning",
    "Deep Learning",
    "Pandas",
    "NumPy",
    "Excel",
    "Power BI",
    "Tableau",
    "Communication",
]


# Required skills for different job roles
ROLE_SKILLS = {
    "Software Developer": [
        "Python", "Java", "C++", "Data Structures",
        "Algorithms", "OOP", "SQL", "Git"
    ],

    "Frontend Developer": [
        "HTML", "CSS", "JavaScript", "React", "Git"
    ],

    "Backend Developer": [
        "Python", "Java", "Flask", "Django",
        "SQL", "PostgreSQL", "Git"
    ],

    "Data Analyst": [
        "Python", "SQL", "Excel", "Pandas",
        "NumPy", "Power BI", "Tableau"
    ],

    "Data Scientist": [
        "Python", "SQL", "Pandas", "NumPy",
        "Machine Learning", "Deep Learning"
    ],

    "Java Developer": [
        "Java", "OOP", "Data Structures",
        "Algorithms", "SQL", "Git"
    ],

    "Python Developer": [
        "Python", "Flask", "Django", "SQL",
        "Git", "Data Structures"
    ]
}


def extract_skills(text):

    found_skills = []

    for skill in SKILLS:

        # Match complete skill names
        pattern = r'(?<!\w)' + re.escape(skill) + r'(?!\w)'

        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill)

    return found_skills


def analyze_skill_gap(found_skills, target_role):

    required_skills = ROLE_SKILLS.get(target_role, [])

    matched_skills = [
        skill for skill in required_skills
        if skill.lower() in [s.lower() for s in found_skills]
    ]

    missing_skills = [
        skill for skill in required_skills
        if skill.lower() not in [s.lower() for s in found_skills]
    ]

    return {
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }
