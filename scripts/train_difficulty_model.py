from sklearn.model_selection import GridSearchCV
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# Load Data
student_assessment = pd.read_csv("../data/oulad/studentAssessment.csv")
assessments = pd.read_csv("../data/oulad/assessments.csv")

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

X_train = X_train[:30000]
y_train = y_train[:30000]

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

param_grids = {
    "LogisticRegression": {
        "model__C": [0.1, 1.0, 10.0]
    },
    "DecisionTreeClassifier": {
        "model__max_depth": [5, 10],
        "model__min_samples_split": [2, 5]
    },
    "RandomForestClassifier": {
        "model__n_estimators": [100, 200],
        "model__max_depth": [10]
    },
    "GradientBoosting": {
        "model__n_estimators": [100, 200],
        "model__learning_rate": [0.1, 0.2]
    }
}

# Fine-tuning loop with GridSearchCV
best_models = {}
for name, pipe in models.items():
    print(f"\n--- Fine-tuning {name} ---")
    grid_search = GridSearchCV(pipe, param_grids[name], cv=5, scoring='accuracy')
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    best_accuracy = grid_search.best_score_

    best_models[name] = best_model
    print(f"Best Accuracy: {best_accuracy:.4f}")
    print(f"Best Parameters: {best_params}")

overall_best_model = max(best_models, key=lambda n: best_models[n].score(X_test, y_test))
print(f"\nFinal Best Model: {overall_best_model}")


comparison_df = pd.DataFrame({
    "Model": list(best_models.keys()),
    "Initial Accuracy": [0.5890, 0.6198, 0.6190, 0.6264],  # Your old numbers
    "Fine-Tuned Accuracy": [best_models[name].score(X_test, y_test) for name in best_models.keys()]
})
print("\n=== FINAL COMPARISON TABLE ===")
print(comparison_df)


comparison_df.to_csv("model_comparison.csv", index=False)
print("Comparison saved to model_comparison.csv")

# Save the fine-tuned model to the exact location Flask expects
os.makedirs("app/ml", exist_ok=True)
joblib.dump({
    "pipeline": best_models[overall_best_model],
    "model_name": overall_best_model,
    "metrics": {"accuracy": best_models[overall_best_model].score(X_test, y_test)},
    "all_results": {"accuracy": best_models[overall_best_model].score(X_test, y_test)},
    "features": NUMERIC + CATEGORICAL,
    "classes": sorted(y.unique().tolist()),
}, "app/ml/difficulty_model.joblib")

print(f"Fine-tuned model saved to app/ml/difficulty_model.joblib")