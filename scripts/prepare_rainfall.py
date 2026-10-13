
from pathlib import Path
import pandas as pd

input_file = Path("data/processed/rajasthan_rainfall_districtwise.csv")
output_file = Path("data/processed/rainfall_daily.csv")

df = pd.read_csv(input_file)

# Keep only the columns needed for the first version
clean_df = df[
    ["Date", "State", "District", "Daily Actual"]
].copy()

# Standardize column names
clean_df = clean_df.rename(columns={
    "Date": "date",
    "State": "state",
    "District": "district",
    "Daily Actual": "rainfall_mm"
})

# Convert date and rainfall values
clean_df["date"] = pd.to_datetime(
    clean_df["date"],
    dayfirst=True,
    errors="coerce"
)

clean_df["rainfall_mm"] = pd.to_numeric(
    clean_df["rainfall_mm"],
    errors="coerce"
)

# Remove records without usable date, district, or rainfall
clean_df = clean_df.dropna(
    subset=["date", "district", "rainfall_mm"]
)

# Keep only valid non-negative rainfall measurements
clean_df = clean_df[clean_df["rainfall_mm"] >= 0]

# Preserve original missing values by excluding unusable records,
# rather than replacing them with zero.
clean_df["data_source"] = "IMD"

output_file.parent.mkdir(parents=True, exist_ok=True)
clean_df.to_csv(output_file, index=False)

print("Cleaned rainfall data saved!")
print("Rows:", len(clean_df))
print("Date range:", clean_df["date"].min(), "to", clean_df["date"].max())
print("Districts:", clean_df["district"].nunique())
print("\nSample:")
print(clean_df.head())
