import pandas as pd
import random
from datetime import datetime
import os

file_path = "/content/Medical_app/health_data_labeled.csv"

# Create file with headers if missing
if not os.path.exists(file_path):
    df = pd.DataFrame(columns=["timestamp", "heart_rate", "blood_oxygen", "activity_level", "anomaly"])
    df.to_csv(file_path, index=False)

# Generate 20 new rows
new_rows = []
for _ in range(20):
    new_rows.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "heart_rate": random.randint(60, 100),
        "blood_oxygen": random.randint(90, 100),
        "activity_level": random.choice(["Low", "Moderate", "High"]),
        "anomaly": random.choice(["Normal", "Anomaly"])
    })

df = pd.DataFrame(new_rows)
df.to_csv(file_path, mode='a', header=False, index=False)
print("✅ Added 20 new rows of simulated data!")
