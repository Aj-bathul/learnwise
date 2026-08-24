import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os

# Load Data
student_assessment = pd.read_csv("data/oulad/studentAssessment.csv")
assessments = pd.read_csv("data/oulad/assessments.csv")

# Feature Engineering
student_assessment["score"] = pd.to_numeric(student_assessment["score"], errors="coerce")
student_assessment["date_submitted"] = pd.to_numeric(student_assessment["date_submitted"], errors="coerce")
assessments["date"] = pd.to_numeric(assessments["date"], errors="coerce")

merged = student_assessment.merge(assessments, on="id_assessment", how="left")
merged = merged.dropna(subset=["score"]).sort_values(["id_student", "date_submitted"])

def bucket(score):
    if score >= 80: return "Hard"
    elif score >= 50: return "Medium"
    else: return "Easy"

rows = []
for student_id, group in merged.groupby("id_student"):
    group = group.reset_index(drop=True)
    prev_score, attempts, prev_difficulty = None, 0, None
    for _, r in group.iterrows():
        attempts += 1
        score = float(r["score"])
        due, submitted = r.get("date"), r.get("date_submitted")
        try:
            time_proxy = abs(float(submitted) - float(due)) if pd.notna(due) and pd.notna(submitted) else 30.0
        except (TypeError, ValueError):
            time_proxy = 30.0
        avg_time = max(5.0, min(120.0, time_proxy * 2))
        if prev_score is not None:
            rows.append({
                "previous_score": prev_score, "attempts": attempts,
                "avg_time_seconds": avg_time, "previous_difficulty": prev_difficulty,
                "next_difficulty": bucket(score),
            })
        prev_score, prev_difficulty = score, bucket(score)

df = pd.DataFrame(rows)

# Train Models
NUMERIC = ["previous_score", "attempts", "avg_time_seconds"]
CATEGORICAL = ["previous_difficulty"]
df["previous_difficulty"] = df["previous_difficulty"].fillna("Easy")
X = df[NUMERIC + CATEGORICAL]
y = df["next_difficulty"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

preprocessor = ColumnTransformer([
    ("num", StandardScaler(), NUMERIC),
    ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
])

models = {
    "LogisticRegression": Pipeline([("prep", preprocessor), ("model", LogisticRegression(max_iter=1000))]),
    "DecisionTreeClassifier": Pipeline([("prep", preprocessor), ("model", DecisionTreeClassifier(max_depth=8, random_state=42))]),
    "RandomForestClassifier": Pipeline([("prep", preprocessor), ("model", RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42))]),
    "GradientBoosting": Pipeline([("prep", preprocessor), ("model", GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42))]),
}

results = {}
for name, pipe in models.items():
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds, average="macro", zero_division=0),
        "recall": recall_score(y_test, preds, average="macro", zero_division=0),
        "f1": f1_score(y_test, preds, average="macro", zero_division=0),
    }
    results[name] = metrics
    print(f"{name} accuracy: {metrics['accuracy']:.4f}")

best_name = max(results, key=lambda n: results[n]["accuracy"])
print(f"Best model: {best_name}")

# Save to the exact location Flask expects
os.makedirs("app/ml", exist_ok=True)
joblib.dump({
    "pipeline": models[best_name],
    "model_name": best_name,
    "metrics": results[best_name],
    "all_results": results,
    "features": NUMERIC + CATEGORICAL,
    "classes": sorted(y.unique().tolist()),
}, "app/ml/difficulty_model.joblib")

print(f"Model saved to app/ml/difficulty_model.joblib")