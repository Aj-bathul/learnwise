

import os
import numpy as np
import pandas as pd

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "oulad"
)


def _bucket(score):
    if score >= 80:
        return "Hard"
    elif score >= 50:
        return "Medium"
    else:
        return "Easy"


def _load_real():
    student_assessment = pd.read_csv(os.path.join(DATA_DIR, "studentAssessment.csv"))
    assessments = pd.read_csv(os.path.join(DATA_DIR, "assessments.csv"))

    # OULAD uses '?' for missing values in some columns — coerce to NaN.
    student_assessment["score"] = pd.to_numeric(student_assessment["score"], errors="coerce")
    student_assessment["date_submitted"] = pd.to_numeric(student_assessment["date_submitted"], errors="coerce")
    assessments["date"] = pd.to_numeric(assessments["date"], errors="coerce")

    merged = student_assessment.merge(assessments, on="id_assessment", how="left")
    merged = merged.dropna(subset=["score"])
    merged = merged.sort_values(["id_student", "date_submitted"])

    rows = []
    for student_id, group in merged.groupby("id_student"):
        group = group.reset_index(drop=True)
        prev_score = None
        attempts = 0
        prev_difficulty = None

        for _, r in group.iterrows():
            attempts += 1
            score = float(r["score"])

            # Proxy for answer time: days between due date and submission,
            # scaled down into a seconds-like range so the feature has
            # meaningful spread. Real per-question timing isn't in OULAD.
            due = r.get("date")
            submitted = r.get("date_submitted")
            try:
                time_proxy = abs(float(submitted) - float(due)) if pd.notna(due) and pd.notna(submitted) else 30.0
            except (TypeError, ValueError):
                time_proxy = 30.0
            avg_time_seconds = max(5.0, min(120.0, time_proxy * 2))

            if prev_score is not None:
                rows.append({
                    "previous_score": prev_score,
                    "attempts": attempts,
                    "avg_time_seconds": avg_time_seconds,
                    "previous_difficulty": prev_difficulty,
                    "next_difficulty": _bucket(score),
                })

            prev_score = score
            prev_difficulty = _bucket(score)

    return pd.DataFrame(rows)


def _generate_synthetic(n_students=800, seed=42):
    rng = np.random.default_rng(seed)
    rows = []

    for _ in range(n_students):
        # Each synthetic student has an underlying "ability" that drives
        # correlated scores over multiple attempts, plus noise.
        ability = rng.normal(60, 20)
        n_attempts = rng.integers(2, 8)

        prev_score = None
        prev_difficulty = None

        for attempt in range(1, n_attempts + 1):
            score = np.clip(ability + rng.normal(0, 12) + attempt * rng.normal(1.5, 1), 0, 100)
            avg_time = np.clip(rng.normal(45, 15) - (score - 50) * 0.15, 5, 120)

            if prev_score is not None:
                rows.append({
                    "previous_score": round(prev_score, 2),
                    "attempts": attempt,
                    "avg_time_seconds": round(avg_time, 2),
                    "previous_difficulty": prev_difficulty,
                    "next_difficulty": _bucket(score),
                })

            prev_score = score
            prev_difficulty = _bucket(score)

    return pd.DataFrame(rows)


def load_training_data():
    required_files = ["studentAssessment.csv", "assessments.csv"]
    if os.path.isdir(DATA_DIR) and all(os.path.exists(os.path.join(DATA_DIR, f)) for f in required_files):
        print(f"Loading real OULAD data from {DATA_DIR}")
        df = _load_real()
        source = "real OULAD dataset"
    else:
        print(f"OULAD files not found in {DATA_DIR} — generating synthetic training data instead.")
        print("Download the real dataset and place the CSVs there, then re-run training.")
        df = _generate_synthetic()
        source = "synthetic data (same schema as OULAD-derived features)"

    return df, source


if __name__ == "__main__":
    df, source = load_training_data()
    print(f"Loaded {len(df)} rows from {source}")
    print(df.head())
    print(df["next_difficulty"].value_counts())
