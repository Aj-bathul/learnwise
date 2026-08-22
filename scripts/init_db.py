
import os
import sys
import getpass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Role, User


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        if not Role.query.filter_by(name="student").first():
            db.session.add(Role(name="student"))
        if not Role.query.filter_by(name="admin").first():
            db.session.add(Role(name="admin"))
        db.session.commit()
        print("Roles ready: student, admin")

        if User.query.join(Role).filter(Role.name == "admin").first():
            print("An admin account already exists — skipping admin creation.")
            return

        print("\nNo admin account found. Let's create one.")
        full_name = input("Admin full name: ").strip() or "Admin"
        email = input("Admin email: ").strip().lower()
        password = getpass.getpass("Admin password (min 8 chars): ")

        admin_role = Role.query.filter_by(name="admin").first()
        admin = User(full_name=full_name, email=email, role_id=admin_role.id)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin account created: {email}")


if __name__ == "__main__":
    run()
