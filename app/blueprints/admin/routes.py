from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.models import db, User, Course, Lesson, Quiz, Question, QuizAttempt, Role
from app.ml.predictor import _load_model

admin_bp = Blueprint("admin", __name__, template_folder="../../templates/admin")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard.home"))
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/")
@login_required
@admin_required
def home():
    stats = {
        "total_users": User.query.count(),
        "total_courses": Course.query.count(),
        "total_attempts": QuizAttempt.query.count(),
    }

    model_bundle = _load_model()
    model_info = None
    if model_bundle:
        model_info = {
            "name": model_bundle.get("model_name"),
            "metrics": model_bundle.get("metrics"),
            "features": model_bundle.get("features"),
            "classes": model_bundle.get("classes"),
        }

    return render_template("admin/home.html", stats=stats, model_info=model_info)


# ---------------------------------------------------------------- Users ----
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


# -------------------------------------------------------------- Courses ----
@admin_bp.route("/courses")
@login_required
@admin_required
def courses():
    all_courses = Course.query.order_by(Course.id.desc()).all()
    return render_template("admin/courses.html", courses=all_courses)


@admin_bp.route("/courses/new", methods=["GET", "POST"])
@login_required
@admin_required
def course_new():
    if request.method == "POST":
        course = Course(
            title=request.form["title"].strip(),
            organization=request.form.get("organization", "").strip() or None,
            description=request.form.get("description", "").strip(),
            skills=request.form.get("skills", "").strip() or None,
            difficulty_level=request.form.get("difficulty_level", "Mixed"),
            category=request.form.get("category", "").strip() or None,
            course_url=request.form.get("course_url", "").strip() or None,
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created.", "success")
        return redirect(url_for("admin.courses"))
    return render_template("admin/course_form.html", course=None)


@admin_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def course_edit(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == "POST":
        course.title = request.form["title"].strip()
        course.organization = request.form.get("organization", "").strip() or None
        course.description = request.form.get("description", "").strip()
        course.skills = request.form.get("skills", "").strip() or None
        course.difficulty_level = request.form.get("difficulty_level", "Mixed")
        course.category = request.form.get("category", "").strip() or None
        course.course_url = request.form.get("course_url", "").strip() or None
        db.session.commit()
        flash("Course updated.", "success")
        return redirect(url_for("admin.courses"))
    return render_template("admin/course_form.html", course=course)


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
@admin_required
def course_delete(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("admin.courses"))


# ------------------------------------------------------------- Lessons -----
@admin_bp.route("/courses/<int:course_id>/lessons/new", methods=["GET", "POST"])
@login_required
@admin_required
def lesson_new(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == "POST":
        lesson = Lesson(
            course_id=course.id,
            title=request.form["title"].strip(),
            video_url=request.form.get("video_url", "").strip() or None,
            content=request.form.get("content", "").strip(),
            order_index=int(request.form.get("order_index", 0) or 0),
        )
        db.session.add(lesson)
        db.session.commit()
        flash("Lesson added.", "success")
        return redirect(url_for("admin.course_edit", course_id=course.id))
    return render_template("admin/lesson_form.html", course=course)


@admin_bp.route("/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def lesson_edit(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if request.method == "POST":
        lesson.title = request.form["title"].strip()
        lesson.video_url = request.form.get("video_url", "").strip() or None
        lesson.content = request.form.get("content", "").strip()
        lesson.order_index = int(request.form.get("order_index", 0) or 0)
        db.session.commit()
        flash("Lesson updated.", "success")
        return redirect(url_for("admin.course_edit", course_id=lesson.course_id))
    return render_template("admin/lesson_form.html", course=lesson.course, lesson=lesson)


@admin_bp.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
@login_required
@admin_required
def lesson_delete(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    db.session.delete(lesson)
    db.session.commit()
    flash("Lesson deleted.", "info")
    return redirect(url_for("admin.course_edit", course_id=course_id))


# -------------------------------------------------------------- Quizzes ----
@admin_bp.route("/courses/<int:course_id>/quizzes/new", methods=["GET", "POST"])
@login_required
@admin_required
def quiz_new(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == "POST":
        quiz = Quiz(course_id=course.id, title=request.form["title"].strip())
        db.session.add(quiz)
        db.session.commit()
        flash("Quiz created. Now add questions.", "success")
        return redirect(url_for("admin.question_new", quiz_id=quiz.id))
    return render_template("admin/quiz_form.html", course=course)


@admin_bp.route("/quizzes/<int:quiz_id>/questions/new", methods=["GET", "POST"])
@login_required
@admin_required
def question_new(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == "POST":
        question = Question(
            quiz_id=quiz.id,
            question_text=request.form["question_text"].strip(),
            option_a=request.form["option_a"].strip(),
            option_b=request.form["option_b"].strip(),
            option_c=request.form["option_c"].strip(),
            option_d=request.form["option_d"].strip(),
            correct_option=request.form["correct_option"],
            difficulty_level=request.form["difficulty_level"],
        )
        db.session.add(question)
        db.session.commit()
        flash("Question added.", "success")
        return redirect(url_for("admin.question_new", quiz_id=quiz.id))
    return render_template("admin/question_form.html", quiz=quiz)


@admin_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@login_required
@admin_required
def question_delete(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.", "info")
    return redirect(url_for("admin.question_new", quiz_id=quiz_id))
