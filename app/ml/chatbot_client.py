

import os
from google import genai

_client = None

SYSTEM_PROMPT = (
    "You are LearnWise's learning support assistant. You help students understand "
    "concepts from their course lessons and quizzes in simple, beginner-friendly terms. "
    "Stay strictly focused on educational content related to the course. "
    "If asked something unrelated to learning/education, politely redirect the "
    "student back to their coursework. Keep answers concise and clear."
)

MODEL_NAME = "gemini-3.5-flash"


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "your-gemini-key-here":
            return None
        _client = genai.Client(api_key=api_key)
    return _client


def ask_chatbot(question, lesson_title=None, course_title=None):
    """Returns a plain-text answer, or a clear message if no API key is configured."""
    client = _get_client()
    if client is None:
        return (
            "The learning assistant isn't connected to an AI provider yet. "
            "Set GEMINI_API_KEY in your .env file to enable real answers."
        )

    context = ""
    if course_title:
        context += f"Course: {course_title}. "
    if lesson_title:
        context += f"Lesson: {lesson_title}. "

    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=f"{SYSTEM_PROMPT}\n\n{context}Student question: {question}",
        )
        return interaction.output_text.strip()
    except Exception as e:
        return f"Sorry, the learning assistant is temporarily unavailable ({type(e).__name__})."
