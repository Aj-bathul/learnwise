from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user

from app.models import db, ChatbotLog, Lesson
from app.ml.chatbot_client import ask_chatbot

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chatbot")
@login_required
def widget():
    return render_template("dashboard/chatbot.html")


@chatbot_bp.route("/chatbot/ask", methods=["POST"])
@login_required
def ask():
    data = request.get_json(force=True) or {}
    question = data.get("question", "").strip()
    lesson_id = data.get("lesson_id")

    if not question:
        return jsonify({"error": "Question is required."}), 400

    lesson_title = None
    course_title = None
    if lesson_id:
        lesson = Lesson.query.get(lesson_id)
        if lesson:
            lesson_title = lesson.title
            course_title = lesson.course.title

    answer = ask_chatbot(question, lesson_title=lesson_title, course_title=course_title)

    log = ChatbotLog(user_id=current_user.id, lesson_id=lesson_id, question=question, response=answer)
    db.session.add(log)
    db.session.commit()

    return jsonify({"answer": answer})
