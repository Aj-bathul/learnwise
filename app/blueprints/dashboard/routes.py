from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint("dashboard", __name__, template_folder="../../templates/dashboard")


@dashboard_bp.route("/dashboard")
@login_required
def home():
    enrollments = current_user.enrollments
    return render_template("dashboard/home.html", enrollments=enrollments)
