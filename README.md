# LearnWise: AI-Assisted Personalised E-Learning Platform

## Project Overview

LearnWise is a web-based personalised e-learning platform built using Python Flask and MySQL. It combines standard Learning Management System features with AI
and Machine Learning support to create a truly adaptive learning experience.

## Key Features

Secure user registration and authentication with password hashing. Browse,
search, and enrol in real courses sourced from the Kaggle Coursera dataset. Watch embedded video lessons and track progress. Take quizzes with AI-predicted difficulty based on historical performance. Get personalised course recommendations from the Gemini API. Use an AI-powered learning support chatbot. Full Admin panel to manage courses, lessons, quizzes, and questions.

## Technology Stack

Backend is developed using Python Flask. Database is managed using MySQL on WampServer.
Object Relational Mapping is handled by Flask-SQLAlchemy. Frontend uses HTML, CSS, Bootstrap 5, and JavaScript. Machine Learning and data processing use scikit-learn, pandas, and joblib. AI Services are powered by the Google Gemini API using the google-genai SDK.

## Machine Learning Model

The adaptive quiz difficulty engine was trained on the Open University Learning
Analytics Dataset (OULAD). Four models were compared: Logistic Regression, Decision Tree,
Random Forest, and Gradient Boosting. Gradient Boosting was selected as the final deployed model with the 
highest accuracy of 62.64 percent. A rule-based fallback system is also included to ensure the quiz system 
continues to work even if the Machine Learning model is unavailable.

## Installation and Setup

1. Clone the repository using the command git clone https://github.com/Aj-bathul/learnwise.git.

2. Create a virtual environment using the command python -m venv venv. On Windows, activate it using venv\Scripts\activate. On Mac or Linux, activate it using source venv/bin/activate.

3. Install all dependencies using the command pip install -r requirements.txt.

4. Create a .env file in the root directory and add the following details: SECRET_KEY=your_secret_key, DATABASE_URL=mysql+pymysql://root:@localhost/learnwise, and GEMINI_API_KEY=your_gemini_api_key.

5. Initialize the database using the command python scripts/init_db.py.

6. Import the course data using the command python scripts/import_courses.py.

7. Run the application using the command python run.py.

## License

This project was developed for academic purposes 
