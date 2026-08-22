

import os
import json
from google import genai

_client = None
MODEL_NAME = "gemini-3.5-flash"


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "your-gemini-key-here":
            return None
        _client = genai.Client(api_key=api_key)
    return _client


def recommend_courses(student_name, interests, completed_courses, candidate_courses, top_n=3):
    """
    completed_courses: list of dicts {title, score_percent}
    candidate_courses: list of dicts {id, title, category, difficulty_level}
    Returns: list of {course_id, reason} or None if no API key configured.
    """
    client = _get_client()
    if client is None:
        return None

    completed_summary = "; ".join(
        f"{c['title']} (scored {c['score_percent']}%)" for c in completed_courses
    ) or "None yet"

    candidates_summary = "\n".join(
        f"id={c['id']}: {c['title']} [{c['category']}, {c['difficulty_level']}]"
        for c in candidate_courses
    )

    prompt = (
        "You are a course recommendation engine. Respond only with valid JSON, no other text.\n\n"
        f"Student: {student_name}. Interests: {interests or 'not specified'}.\n"
        f"Completed courses: {completed_summary}.\n\n"
        f"Candidate courses to choose from:\n{candidates_summary}\n\n"
        f"Pick the {top_n} best next courses for this student from the candidates above ONLY "
        f"(use their exact id values). Respond ONLY with a JSON array like: "
        f'[{{"course_id": 12, "reason": "short one-sentence reason"}}, ...]. No other text.'
    )

    try:
        interaction = client.interactions.create(model=MODEL_NAME, input=prompt)
        raw = interaction.output_text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception:
        return None
