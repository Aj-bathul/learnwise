from flask import Flask, redirect, url_for, render_template  # Added render_template here
from flask_login import LoginManager, current_user

from config import Config
from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---- Register blueprints ----
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.dashboard.routes import dashboard_bp
    from app.blueprints.courses.routes import courses_bp
    from app.blueprints.quizzes.routes import quizzes_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.chatbot.routes import chatbot_bp
    from app.blueprints.recommend.routes import recommend_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(quizzes_bp, url_prefix="/quizzes")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    app.register_blueprint(recommend_bp, url_prefix="/recommend")

    @app.route("/")
    def index():
        """Root route - landing page for everyone"""
        return render_template("landing.html")

    return app