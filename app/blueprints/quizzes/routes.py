import time
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user

from app.models import db, Quiz, Question, QuizAttempt

quizzes_bp = Blueprint("quizzes", __name__, template_folder="../../templates/quizzes")


@quizzes_bp.route("/quizzes/<int:quiz_id>")
@login_required
def take(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    #difiiculty predicted from therir last effort
    from app.ml.predictor import predict_difficulty

    target_difficulty = predict_difficulty(current_user.id, quiz_id)

    questions = Question.query.filter_by(
        quiz_id=quiz_id, difficulty_level=target_difficulty
    ).all()
    if not questions:
        # Fallback: if there aren't enough questions at the predicted
        # difficulty yet, just serve whatever exists for this quiz.
        questions = Question.query.filter_by(quiz_id=quiz_id).all()

    session["quiz_start_time"] = time.time()

    return render_template(
        "quizzes/take.html", quiz=quiz, questions=questions, difficulty=target_difficulty
    )


@quizzes_bp.route("/quizzes/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    start_time = session.pop("quiz_start_time", time.time())
    elapsed = max(time.time() - start_time, 1)

    question_ids = request.form.getlist("question_id")
    total = len(question_ids)
    correct = 0

    for qid in question_ids:
        question = Question.query.get(int(qid))
        submitted_answer = request.form.get(f"answer_{qid}")
        if submitted_answer and submitted_answer.upper() == question.correct_option:
            correct += 1

    score_percent = round((correct / total) * 100, 2) if total else 0
    avg_time = round(elapsed / total, 2) if total else 0

    previous_attempt = (
        QuizAttempt.query.filter_by(user_id=current_user.id, quiz_id=quiz_id)
        .order_by(QuizAttempt.attempted_at.desc())
        .first()
    )
    attempt_number = (previous_attempt.attempt_number + 1) if previous_attempt else 1
    previous_difficulty = previous_attempt.predicted_next_difficulty if previous_attempt else None

    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        total_questions=total,
        correct_answers=correct,
        score_percent=score_percent,
        avg_answer_time_seconds=avg_time,
        attempt_number=attempt_number,
        previous_difficulty=previous_difficulty,
    )
    db.session.add(attempt)
    db.session.commit()

    # Predict the difficulty for this student's NEXT attempt and log it.
    from app.ml.predictor import predict_and_log

    predict_and_log(attempt)

    flash(f"You scored {correct}/{total} ({score_percent}%)", "success")
    return redirect(url_for("quizzes.result", attempt_id=attempt.id))


@quizzes_bp.route("/quizzes/attempts/<int:attempt_id>")
@login_required
def result(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        flash("You don't have access to that result.", "danger")
        return redirect(url_for("dashboard.home"))
    return render_template("quizzes/result.html", attempt=attempt)
