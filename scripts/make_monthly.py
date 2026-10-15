import pandas as pd

# 1. Load the daily data
df = pd.read_csv("data/processed/rainfall_daily.csv")

# 2. Clean it
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["district"] = df["district"].str.strip().str.title()
df = df.dropna(subset=["date", "district", "rainfall_mm"])
df = df.drop_duplicates(subset=["district", "date"])   # one row per district per day

# 3. Add year and month columns
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# 4. Total rainfall for each district, year and month
monthly_totals = df.groupby(["district", "year", "month"])["rainfall_mm"].sum().reset_index()

# 5. Average each month across the years
result = monthly_totals.groupby(["district", "month"])["rainfall_mm"].mean().round(1).reset_index()
result = result.rename(columns={"rainfall_mm": "avg_rainfall_mm"})

# 6. Save
result.to_csv("data/processed/monthly_rainfall_by_district.csv", index=False)

# 7. Quick check
print("Districts:", result["district"].nunique())
print("\nJalore:")
print(result[result["district"] == "Jalore"])
print("\nYearly total for Jalore:", result[result["district"] == "Jalore"]["avg_rainfall_mm"].sum())