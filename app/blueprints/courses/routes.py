from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.models import db, Course, Enrollment, Lesson

courses_bp = Blueprint("courses", __name__, template_folder="../../templates/courses")


def get_embed_url(video_url):

    if not video_url:
        return None

    # Clean up the URL
    video_url = video_url.strip()

    # If it's already an embed URL
    if 'youtube.com/embed/' in video_url:
        return video_url

    # Handle youtube.com/watch?v= format
    if 'watch?v=' in video_url:
        video_id = video_url.split('v=')[1].split('&')[0]
        return f'https://www.youtube.com/embed/{video_id}'

    # Handle youtu.be/ format
    if 'youtu.be/' in video_url:
        video_id = video_url.split('/')[-1].split('?')[0]
        return f'https://www.youtube.com/embed/{video_id}'

    # Handle youtube.com/shorts/ format
    if 'shorts/' in video_url:
        video_id = video_url.split('/')[-1].split('?')[0]
        return f'https://www.youtube.com/embed/{video_id}'

    # Handle youtube.com/embed/ format with extra parameters
    if '/embed/' in video_url:
        # Already an embed URL
        return video_url

    # If none of the above, return original
    return video_url


@courses_bp.route("/courses")
def browse():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = Course.query
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))
    if category:
        query = query.filter(Course.category == category)

    courses = query.order_by(Course.rating.desc()).limit(60).all()
    categories = [c[0] for c in db.session.query(Course.category).distinct() if c[0]]

    return render_template(
        "courses/browse.html", courses=courses, categories=categories, search=search
    )


@courses_bp.route("/courses/<int:course_id>")
def detail(course_id):
    course = Course.query.get_or_404(course_id)
    is_enrolled = False
    if current_user.is_authenticated:
        is_enrolled = Enrollment.query.filter_by(
            user_id=current_user.id, course_id=course.id
        ).first() is not None
    return render_template("courses/detail.html", course=course, is_enrolled=is_enrolled)


@courses_bp.route("/courses/<int:course_id>/enroll", methods=["POST"])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)

    existing = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if existing:
        flash("You're already enrolled in this course.", "info")
        return redirect(url_for("courses.detail", course_id=course.id))

    enrollment = Enrollment(user_id=current_user.id, course_id=course.id)
    db.session.add(enrollment)
    db.session.commit()

    flash(f"Enrolled in {course.title}!", "success")
    return redirect(url_for("courses.detail", course_id=course.id))


@courses_bp.route("/lessons/<int:lesson_id>")
@login_required
def lesson_view(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course

    embed_url = get_embed_url(lesson.video_url)

    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if enrollment is None:
        flash("Enroll in this course to watch its lessons.", "info")
        return redirect(url_for("courses.detail", course_id=course.id))

    # Bump progress based on how many lessons the student has "opened" so far
    all_lessons = sorted(course.lessons, key=lambda l: l.order_index)
    if lesson in all_lessons:
        position = all_lessons.index(lesson) + 1
        progress = round((position / len(all_lessons)) * 100, 2)
        if progress > float(enrollment.progress_percent):
            enrollment.progress_percent = progress
            if progress >= 100:
                enrollment.status = "completed"
            db.session.commit()

    next_lesson = None
    idx = all_lessons.index(lesson) if lesson in all_lessons else -1
    if 0 <= idx < len(all_lessons) - 1:
        next_lesson = all_lessons[idx + 1]

    quiz = course.quizzes[0] if course.quizzes else None

    return render_template(
        "courses/lesson.html",
        lesson=lesson,
        course=course,
        next_lesson=next_lesson,
        quiz=quiz,
        enrollment=enrollment,
        embed_url=embed_url
    )