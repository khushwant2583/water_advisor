
from pathlib import Path
import pandas as pd

file_path = Path("data/raw/rainfall_districtwise_daily_imd.csv")

if not file_path.exists():
    raise FileNotFoundError(
        f"Dataset not found: {file_path}. "
        "Check the filename and folder."
    )

df = pd.read_csv(file_path)

print("\n--- Dataset shape ---")
print(df.shape)

print("\n--- Column names ---")
print(df.columns.tolist())

print("\n--- First five rows ---")
print(df.head())

print("\n--- Data types ---")
print(df.dtypes)

print("\n--- Missing values ---")
print(df.isna().sum())
