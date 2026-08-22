
import os
import sys
import random
import argparse
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Course

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "coursea_data.csv")
MAX_COURSES = 30

CATEGORY_KEYWORDS = {
    "Data Science": ["data", "machine learning", "statistics", "analytics", "python for data"],
    "Web Development": ["web", "html", "css", "javascript", "front-end", "full stack"],
    "Programming": ["python", "java", "c++", "programming", "algorithms", "coding"],
    "Business": ["business", "marketing", "finance", "management", "leadership"],
    "Cloud & DevOps": ["cloud", "aws", "azure", "devops", "docker", "kubernetes"],
    "Design": ["design", "ux", "ui", "graphic"],
}


def guess_category(title):
    title_lower = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in title_lower for k in keywords):
            return category
    return "General"


def load_dataframe():
    if os.path.exists(DATA_PATH):
        print(f"Loading real dataset from {DATA_PATH}")
        df = pd.read_csv(DATA_PATH)
        return df, True

    print(f"No dataset found at {DATA_PATH} — generating a sample dataset instead.")
    print("Download the real one from Kaggle and re-run this script to replace it.")

    sample_titles = [
        ("Python for Everybody", "University of Michigan"),
        ("Machine Learning", "Stanford University"),
        ("Introduction to HTML5", "University of Michigan"),
        ("The Complete Web Developer Course", "Coursera Project Network"),
        ("Data Science Fundamentals", "IBM"),
        ("Deep Learning Specialization", "DeepLearning.AI"),
        ("Google Cloud Fundamentals", "Google Cloud"),
        ("AWS Cloud Practitioner Essentials", "Amazon Web Services"),
        ("UX Design Basics", "California Institute of the Arts"),
        ("Business Analytics", "University of Pennsylvania"),
        ("Excel Skills for Business", "Macquarie University"),
        ("JavaScript Algorithms and Data Structures", "freeCodeCamp"),
        ("Introduction to Docker", "IBM"),
        ("Financial Markets", "Yale University"),
        ("Agile Project Management", "Google"),
        ("SQL for Data Science", "University of California, Davis"),
        ("Full-Stack Web Development with React", "The Hong Kong University of Science and Technology"),
        ("Cybersecurity Fundamentals", "IBM"),
        ("Digital Marketing Strategy", "University of Illinois"),
        ("Introduction to Statistics", "Stanford University"),
    ]

    rows = []
    for title, org in sample_titles:
        rows.append({
            "course_title": title,
            "course_organization": org,
            "course_Certificate_type": random.choice(["COURSE", "SPECIALIZATION", "PROFESSIONAL CERTIFICATE"]),
            "course_rating": round(random.uniform(3.9, 5.0), 1),
            "course_difficulty": random.choice(["Beginner", "Intermediate", "Advanced", "Mixed"]),
            "course_students_enrolled": f"{random.randint(5, 900)}k",
        })
    return pd.DataFrame(rows), False


def select_curated_subset(df, limit):
    """
    Picks `limit` courses spread across categories (round-robin), each
    category's own courses sorted by rating descending — so we get variety
    rather than e.g. 30 courses that all happen to be Business courses.
    """
    df = df.copy()
    df["_rating_num"] = pd.to_numeric(df.get("course_rating"), errors="coerce").fillna(0)
    df["_category"] = df["course_title"].astype(str).apply(guess_category)

    grouped = {
        category: group.sort_values("_rating_num", ascending=False).to_dict("records")
        for category, group in df.groupby("_category")
    }
    # Stable, deterministic category order
    categories = sorted(grouped.keys())

    selected = []
    idx = 0
    while len(selected) < limit and any(grouped[c] for c in categories):
        category = categories[idx % len(categories)]
        if grouped[category]:
            selected.append(grouped[category].pop(0))
        idx += 1

    return pd.DataFrame(selected).drop(columns=["_rating_num", "_category"], errors="ignore")


def parse_enrolled_count(value):
    """Kaggle dataset stores this like '1.2m' or '54k' — convert to an int review-count proxy."""
    if pd.isna(value):
        return None
    value = str(value).strip().lower()
    try:
        if value.endswith("m"):
            return int(float(value[:-1]) * 1_000_000)
        if value.endswith("k"):
            return int(float(value[:-1]) * 1_000)
        return int(float(value))
    except ValueError:
        return None


def run(limit=MAX_COURSES):
    app = create_app()
    with app.app_context():
        df, is_real = load_dataframe()
        df = df.dropna(subset=["course_title"])
        df = df.drop_duplicates(subset=["course_title"])

        if len(df) > limit:
            df = select_curated_subset(df, limit)

        imported = 0
        for _, row in df.iterrows():
            title = str(row.get("course_title", "")).strip()
            if not title:
                continue

            if Course.query.filter_by(title=title).first():
                continue  # skip duplicates on re-run

            organization = str(row.get("course_organization", "")).strip() or None
            difficulty = str(row.get("course_difficulty", "Mixed")).strip().title()
            if difficulty not in ("Beginner", "Intermediate", "Advanced", "Mixed"):
                difficulty = "Mixed"

            rating = row.get("course_rating")
            try:
                rating = round(float(rating), 2) if pd.notna(rating) else None
            except (ValueError, TypeError):
                rating = None

            review_count = parse_enrolled_count(row.get("course_students_enrolled"))

            course = Course(
                source_course_id=str(row.get("course_id", "")) or None,
                title=title,
                organization=organization,
                description=f"{title} offered by {organization or 'an online learning partner'}. "
                             f"Certificate type: {row.get('course_Certificate_type', 'N/A')}.",
                skills=None,
                difficulty_level=difficulty,
                rating=rating,
                review_count=review_count,
                course_url=None,
                category=guess_category(title),
            )
            db.session.add(course)
            imported += 1

        db.session.commit()
        source = "real Kaggle dataset" if is_real else "generated sample data"
        print(f"Imported {imported} courses (limit={limit}) from {source}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=MAX_COURSES, help="Max number of courses to import")
    args = parser.parse_args()
    run(limit=args.limit)
