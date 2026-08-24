from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import db, Course, Enrollment, QuizAttempt, Recommendation, Quiz
from app.ml.recommender import recommend_courses

recommend_bp = Blueprint("recommend", __name__, template_folder="../../templates/dashboard")


@recommend_bp.route("/recommendations")
@login_required
def home():
    enrolled_ids = [e.course_id for e in current_user.enrollments]

    completed = []
    for e in current_user.enrollments:
        if e.status == "completed":
            best_attempt = (
                QuizAttempt.query.join(Quiz)
                .filter(Quiz.course_id == e.course_id, QuizAttempt.user_id == current_user.id)
                .order_by(QuizAttempt.score_percent.desc())
                .first()
            )
            completed.append({
                "title": e.course.title,
                "score_percent": float(best_attempt.score_percent) if best_attempt else None,
            })

    candidates = Course.query.filter(~Course.id.in_(enrolled_ids)).limit(30).all() if enrolled_ids \
        else Course.query.limit(30).all()

    candidate_dicts = [
        {"id": c.id, "title": c.title, "category": c.category, "difficulty_level": c.difficulty_level}
        for c in candidates
    ]

    suggestions = []
    ai_reasons = {}

    if completed and candidate_dicts:
        ai_result = recommend_courses(
            student_name=current_user.full_name,
            interests=current_user.interests,
            completed_courses=completed,
            candidate_courses=candidate_dicts,
        )
        if ai_result:
            id_to_course = {c.id: c for c in candidates}
            for item in ai_result:
                course = id_to_course.get(item.get("course_id"))
                if course:
                    suggestions.append(course)
                    ai_reasons[course.id] = item.get("reason", "")
                    # Log it so admins/analytics can see recommendation history
                    db.session.add(Recommendation(
                        user_id=current_user.id,
                        recommended_course_id=course.id,
                        reason=item.get("reason", ""),
                    ))
            db.session.commit()

    if not suggestions:
        # Fallback when no API key is set, or student hasn't completed a course yet:

        suggestions = candidates[:3]

    return render_template(
        "dashboard/recommendations.html", suggestions=suggestions, ai_reasons=ai_reasons
    )
