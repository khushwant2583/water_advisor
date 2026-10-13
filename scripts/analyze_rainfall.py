
from pathlib import Path
import pandas as pd

input_file = Path("data/processed/rainfall_daily.csv")
output_file = Path("data/processed/annual_rainfall_summary.csv")

# Load cleaned Rajasthan rainfall data
df = pd.read_csv(input_file)

# Validate required columns
required_columns = {"date", "district", "rainfall_mm"}
missing = required_columns - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {missing}")

# Convert values into appropriate data types
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["rainfall_mm"] = pd.to_numeric(
    df["rainfall_mm"], errors="coerce"
)

# Remove unusable records
df = df.dropna(subset=["date", "district", "rainfall_mm"])
df = df[df["rainfall_mm"] >= 0].copy()

# Extract year
df["year"] = df["date"].dt.year

# Calculate recorded rainfall for each district and year
summary = (
    df.groupby(["district", "year"], as_index=False)
    .agg(
        recorded_rainfall_mm=("rainfall_mm", "sum"),
        observation_count=("rainfall_mm", "count"),
        first_observation=("date", "min"),
        last_observation=("date", "max"),
    )
)

output_file.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(output_file, index=False)

print("\n--- Rainfall analysis complete ---")
print("Input records:", len(df))
print("Districts:", df["district"].nunique())
print("Years:", sorted(df["year"].unique()))
print("\nSample summary:")
print(summary.head(10))
print("\nSaved to:", output_file.resolve())
