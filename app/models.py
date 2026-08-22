

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    users = db.relationship("User", backref="role", lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    interests = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def is_admin(self):
        return self.role.name == "admin"


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    source_course_id = db.Column(db.String(100))
    title = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(150))
    description = db.Column(db.Text)
    skills = db.Column(db.String(500))
    difficulty_level = db.Column(
        db.Enum("Beginner", "Intermediate", "Advanced", "Mixed"), default="Mixed"
    )
    rating = db.Column(db.Numeric(3, 2))
    review_count = db.Column(db.Integer)
    course_url = db.Column(db.String(500))
    category = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lessons = db.relationship("Lesson", backref="course", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", backref="course", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", backref="course", cascade="all, delete-orphan")


class Lesson(db.Model):
    __tablename__ = "lessons"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    video_url = db.Column(db.String(500))
    content = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum("active", "completed", "dropped"), default="active")
    progress_percent = db.Column(db.Numeric(5, 2), default=0.00)

    user = db.relationship("User", backref="enrollments")

    __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uniq_enrollment"),)


class Quiz(db.Model):
    __tablename__ = "quizzes"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"))
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship("Question", backref="quiz", cascade="all, delete-orphan")
    attempts = db.relationship("QuizAttempt", backref="quiz", cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Enum("A", "B", "C", "D"), nullable=False)
    difficulty_level = db.Column(db.Enum("Easy", "Medium", "Hard"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    score_percent = db.Column(db.Numeric(5, 2), nullable=False)
    avg_answer_time_seconds = db.Column(db.Numeric(6, 2), nullable=False)
    attempt_number = db.Column(db.Integer, default=1)
    previous_difficulty = db.Column(db.Enum("Easy", "Medium", "Hard"))
    predicted_next_difficulty = db.Column(db.Enum("Easy", "Medium", "Hard"))
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="quiz_attempts")
    predictions = db.relationship("MLPrediction", backref="attempt", cascade="all, delete-orphan")


class MLPrediction(db.Model):
    __tablename__ = "ml_predictions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempts.id"), nullable=False)
    predicted_difficulty = db.Column(db.Enum("Easy", "Medium", "Hard"), nullable=False)
    model_used = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Numeric(5, 4))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatbotLog(db.Model):
    __tablename__ = "chatbot_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"))
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Recommendation(db.Model):
    __tablename__ = "recommendations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recommended_course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
