import json
from backend.services.ai_service import client, MODEL_NAME


def evaluate_all_answers(evaluation_items, job_role, difficulty):

    prompt = f"""
    You are an expert interview evaluator for PrepAI.

    Job Role: {job_role}
    Difficulty: {difficulty}

    Evaluate each of the following interview question-answer pairs.

    QUESTIONS AND ANSWERS:
    {json.dumps(evaluation_items)}

    For EACH answer evaluate:
    1. Technical correctness
    2. Relevance
    3. Completeness
    4. Clarity
    5. Missing concepts
    6. Suggestions for improvement
    7. An improved answer

    Give a score out of 10 for each answer.

    Return ONLY valid JSON in this format:

    {{
        "evaluations": [
            {{
                "question_id": 1,
                "score": 8,
                "correctness": "...",
                "relevance": "...",
                "completeness": "...",
                "clarity": "...",
                "missing_concepts": ["Concept 1"],
                "feedback": "...",
                "improved_answer": "..."
            }}
        ]
    }}

    Return exactly one evaluation for every supplied question.
    Preserve the question_id for each evaluation.
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are an expert interview evaluator. Return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )

    response_text = response.choices[0].message.content

    result = json.loads(response_text)

    evaluations = result.get("evaluations")

    if not isinstance(evaluations, list):
        raise ValueError("Invalid evaluation response.")

    if len(evaluations) != len(evaluation_items):
        raise ValueError("Incorrect number of evaluations.")

    expected_ids = [item["question_id"] for item in evaluation_items]
    returned_ids = [item.get("question_id") for item in evaluations]

    if sorted(returned_ids) != sorted(expected_ids):
        raise ValueError("Evaluation question IDs do not match.")

    for evaluation in evaluations:

        score = evaluation.get("score")

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not 0 <= score <= 10
        ):
            raise ValueError("Invalid evaluation score.")

    evaluation_map = {
        evaluation["question_id"]: evaluation
        for evaluation in evaluations
    }

    return [
        evaluation_map[question_id]
        for question_id in expected_ids
    ]