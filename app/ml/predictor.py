import os
import joblib
import pandas as pd

from app.models import db, QuizAttempt, MLPrediction

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "difficulty_model.joblib")

_model_cache = None


def _load_model():
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    if os.path.exists(MODEL_PATH):
        try:
            _model_cache = joblib.load(MODEL_PATH)
            print(f"Model loaded successfully: {_model_cache.get('model_name', 'Unknown')}")
        except Exception as e:
            print(f"Model load failed: {e}")
            _model_cache = None
    else:
        print(f"Model file not found at path: {MODEL_PATH}")
    return _model_cache


def _rule_based_predict(score):
    if score is None:
        return "Easy"
    if score >= 80:
        return "Hard"
    elif score >= 50:
        return "Medium"
    else:
        return "Easy"


def _build_features(user_id, quiz_id, exclude_attempt_id=None):
    query = QuizAttempt.query.filter_by(user_id=user_id, quiz_id=quiz_id)
    if exclude_attempt_id:
        query = query.filter(QuizAttempt.id != exclude_attempt_id)
    history = query.order_by(QuizAttempt.attempted_at.asc()).all()

    if not history:
        return None

    last = history[-1]
    previous_difficulty = last.predicted_next_difficulty or _rule_based_predict(float(last.score_percent))

    return {
        "previous_score": float(last.score_percent),
        "attempts": len(history) + 1,
        "avg_time_seconds": float(last.avg_answer_time_seconds),
        "previous_difficulty": previous_difficulty,
    }, float(last.score_percent)


def _predict_from_features(features):
    model_bundle = _load_model()
    if model_bundle is None:
        return None, None, "RuleBasedFallback"

    pipeline = model_bundle["pipeline"]
    model_name = model_bundle["model_name"]

    X = pd.DataFrame([features])

    try:
        prediction = pipeline.predict(X)[0]
    except Exception as e:
        print(f"Prediction failed: {e}")
        return None, None, "RuleBasedFallback"

    if isinstance(prediction, list):
        prediction = prediction[0] if prediction else "Medium"

    confidence = None
    try:
        if hasattr(pipeline, "predict_proba"):
            proba = pipeline.predict_proba(X)[0]
            confidence = round(float(max(proba)), 4)
    except:
        pass

    return prediction, confidence, model_name


def predict_difficulty(user_id, quiz_id):
    """Used when a student STARTS a quiz — decides which question set to serve."""
    built = _build_features(user_id, quiz_id)
    if built is None:
        return "Easy"  # first-ever attempt on this quiz

    features, last_score = built

    print("="*60)
    print(" PREDICTING DIFFICULTY")
    print(f"   User ID: {user_id}")
    print(f"   Quiz ID: {quiz_id}")
    print(f"   Features: {features}")

    prediction, _, _ = _predict_from_features(features)

    print(f"   Prediction: {prediction} (type: {type(prediction).__name__})")
    print("="*60)

    return prediction or _rule_based_predict(last_score)


def predict_and_log(attempt: QuizAttempt):
    """Used right after a student SUBMITS a quiz — predicts + stores the
    difficulty to serve on their NEXT attempt of this quiz."""
    features = {
        "previous_score": float(attempt.score_percent),
        "attempts": attempt.attempt_number + 1,
        "avg_time_seconds": float(attempt.avg_answer_time_seconds),
        "previous_difficulty": attempt.previous_difficulty or _rule_based_predict(float(attempt.score_percent)),
    }

    prediction, confidence, model_name = _predict_from_features(features)
    if prediction is None:
        prediction = _rule_based_predict(float(attempt.score_percent))

    attempt.predicted_next_difficulty = prediction

    log = MLPrediction(
        user_id=attempt.user_id,
        quiz_attempt_id=attempt.id,
        predicted_difficulty=prediction,
        model_used=model_name,
        confidence_score=confidence,
    )
    db.session.add(log)
    db.session.commit()

    return prediction