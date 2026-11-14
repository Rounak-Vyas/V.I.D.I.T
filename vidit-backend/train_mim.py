import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

np.random.seed(42)
n_samples = 270  # 90 days x 3 meals per day

# 1. Synthesize Input Features from V.I.D.I.T Flowchart
# Meal: 0=Breakfast, 1=Lunch, 2=Dinner
# Day: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
data = pd.DataFrame({
    "meal": np.random.choice([0, 1, 2], n_samples),
    "day_of_week": np.random.randint(0, 7, n_samples),
    "exam_period": np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
    "is_holiday": np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
    "special_meal": np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
    "weather_rain": np.random.choice([0, 1], n_samples, p=[0.75, 0.25]),
    "hostel_occupancy": np.random.randint(200, 300, n_samples)
})

# 2. Calculate Realistic Attendance Factor (Multiplier between 0.35 and 0.98)
base_factor = 0.72
factor = (
    base_factor
    - 0.09 * ((data["day_of_week"] == 4) & (data["meal"] == 2))  # Friday Dinner outing drop
    - 0.06 * data["exam_period"]                                 # Exam schedule variance
    - 0.14 * data["is_holiday"]                                  # Holiday drop
    + 0.15 * data["special_meal"]                                # Special menu boost
    + 0.06 * data["weather_rain"]                                # Rain keeps students on campus
    + np.random.normal(0, 0.025, n_samples)                      # Natural daily noise
)

data["attendance_factor"] = np.clip(factor, 0.35, 0.98).round(3)
data["actual_mess_turnout"] = (data["hostel_occupancy"] * data["attendance_factor"]).round().astype(int)

# Save synthetic dataset to CSV so you can inspect or showcase it
data.to_csv("synthetic_mess_data.csv", index=False)
print("Saved 270 synthetic meal records to 'synthetic_mess_data.csv'")

# 3. Train the Random Forest Model
features = ["meal", "day_of_week", "exam_period", "is_holiday", "special_meal", "weather_rain"]
X = data[features]
y = data["attendance_factor"]

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Save the trained model
joblib.dump(model, "mim_model.pkl")
print("Saved trained model to 'mim_model.pkl'\n")

# 4. Test with the exact V.I.D.I.T Flowchart Scenario:
# Meal=Dinner(2), Day=Friday(4), Exam=Midsems(1), Holiday=No(0), Special=No(0), Weather=Rain(1), Occupancy=250
test_input = pd.DataFrame([[2, 4, 1, 0, 0, 1]], columns=features)
tree_preds = np.array([tree.predict(test_input.values)[0] for tree in model.estimators_])

pred_factor = round(float(np.mean(tree_preds)), 2)
confidence_margin = round(float(1.96 * np.std(tree_preds)), 2)
current_occupancy = 250

expected_students = int(round(current_occupancy * pred_factor))
min_range = int(round(current_occupancy * (pred_factor - confidence_margin)))
max_range = int(round(current_occupancy * (pred_factor + confidence_margin)))

print("=== V.I.D.I.T Mess Intelligence Model (MIM) Test ===")
print(f"Attendance Factor : {pred_factor}")
print(f"Confidence        : +/- {confidence_margin}")
print(f"Hostel Occupancy  : {current_occupancy}")
print(f"Prepare For       : {expected_students} students (Range: {min_range} - {max_range})")