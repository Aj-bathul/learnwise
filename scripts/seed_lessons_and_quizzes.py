

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Course, Lesson, Quiz, Question

LESSON_TEMPLATES = [
    "Introduction and Overview",
    "Core Concepts",
    "Hands-on Practice",
    "Advanced Topics",
    "Final Project and Recap",
]


QUESTION_BANK = {
    "Easy": [
        {
            "q": "What is the main topic covered in the course '{topic}'?",
            "options": ["A directly related core skill", "An unrelated hobby", "A cooking technique", "A sports strategy"],
            "correct": "A",
        },
        {
            "q": "In '{topic}', what should you do before starting the first lesson?",
            "options": ["Review the course overview", "Skip all instructions", "Delete your notes", "Ignore prerequisites"],
            "correct": "A",
        },
        {
            "q": "True or false style: '{topic}' includes an introduction section for beginners.",
            "options": ["True", "False", "Not applicable", "Unknown"],
            "correct": "A",
        },
    ],
    "Medium": [
        {
            "q": "Which approach best demonstrates applying the core concept taught in '{topic}'?",
            "options": ["Practicing with a guided exercise", "Avoiding practice entirely", "Only watching without doing", "Skipping the concept"],
            "correct": "A",
        },
        {
            "q": "When working through '{topic}', what's a common mistake learners should avoid?",
            "options": ["Rushing without understanding fundamentals", "Taking notes", "Asking questions", "Reviewing lesson material"],
            "correct": "A",
        },
        {
            "q": "In '{topic}', how would you troubleshoot a problem in a hands-on exercise?",
            "options": ["Break it into smaller steps and test each", "Give up immediately", "Ignore the error", "Restart the whole course"],
            "correct": "A",
        },
    ],
    "Hard": [
        {
            "q": "For an advanced learner of '{topic}', which strategy best demonstrates mastery?",
            "options": ["Applying concepts to a novel, unguided project", "Re-reading the syllabus only", "Memorizing definitions only", "Avoiding practical exercises"],
            "correct": "A",
        },
        {
            "q": "Which scenario best reflects an expert-level understanding of '{topic}'?",
            "options": ["Teaching or explaining the concept to someone else", "Only completing multiple-choice quizzes", "Watching videos passively", "Skipping the final project"],
            "correct": "A",
        },
        {
            "q": "In a complex real-world application of '{topic}', what matters most?",
            "options": ["Evaluating tradeoffs and edge cases", "Following one rigid rule always", "Ignoring context", "Avoiding evaluation"],
            "correct": "A",
        },
    ],
}


def run():
    app = create_app()
    with app.app_context():
        courses = Course.query.all()
        lesson_count = 0
        quiz_count = 0
        question_count = 0

        for course in courses:
            if course.lessons:
                continue  # already seeded

            for i, lesson_title in enumerate(LESSON_TEMPLATES):
                lesson = Lesson(
                    course_id=course.id,
                    title=f"{lesson_title}",
                    video_url=None,
                    content=f"Lesson content for '{lesson_title}' in {course.title}.",
                    order_index=i,
                )
                db.session.add(lesson)
                lesson_count += 1

            db.session.flush()  # get lesson IDs assigned

            quiz = Quiz(course_id=course.id, lesson_id=None, title=f"{course.title} — Assessment")
            db.session.add(quiz)
            db.session.flush()
            quiz_count += 1

            for difficulty, templates in QUESTION_BANK.items():
                for t in templates:
                    options = list(t["options"])
                    question = Question(
                        quiz_id=quiz.id,
                        question_text=t["q"].format(topic=course.title),
                        option_a=options[0],
                        option_b=options[1],
                        option_c=options[2],
                        option_d=options[3],
                        correct_option=t["correct"],
                        difficulty_level=difficulty,
                    )
                    db.session.add(question)
                    question_count += 1

        db.session.commit()
        print(f"Seeded {lesson_count} lessons, {quiz_count} quizzes, {question_count} questions.")


if __name__ == "__main__":
    run()
