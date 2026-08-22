from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.models import db, User, Role

auth_bp = Blueprint("auth", __name__, template_folder="../../templates/auth")


@auth_bp.route("/landing")
def landing():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for("admin.home"))
        return redirect(url_for("dashboard.home"))
    return render_template("auth/landing.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for("admin.home"))
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        interests = request.form.get("interests", "").strip()


        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html")

        student_role = Role.query.filter_by(name="student").first()

        new_user = User(
            full_name=full_name,
            email=email,
            role_id=student_role.id,
            interests=interests,
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # ✅ Green success message
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for("admin.home"))
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):

            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        login_user(user)


        flash(f"Welcome back, {user.full_name}!", "success")

        if user.is_admin():
            return redirect(url_for("admin.home"))

        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard.home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.landing"))