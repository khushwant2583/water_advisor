from pathlib import Path
import pandas as pd
from rapidfuzz import process

UNIT_TO_SQM = {"sqm": 1.0, "sqft": 0.0929, "sqyd": 0.8361, "gaj": 0.8361}


def load_districts():
    f = Path("data/processed/monthly_rainfall_by_district.csv")
    if f.exists():
        return sorted(pd.read_csv(f)["district"].str.strip().str.title().unique())
    return ["Jalore", "Jodhpur", "Jaisalmer", "Barmer", "Jaipur"]  


DISTRICTS = load_districts()


def match_district(text):
    m = process.extractOne(text.strip().title(), DISTRICTS, score_cutoff=75)
    return m[0] if m else None


def lookup_soil(district):
    f = Path("data/processed/district_soil.csv")   
    if not f.exists():
        return None
    df = pd.read_csv(f)
    row = df[df["district"].str.strip().str.title() == district]
    return row["soil_type"].iloc[0] if len(row) else None


def merge_profile(profile, args):
   
    problems = []

    if "district" in args:
        d = match_district(args["district"])
        if d:
            profile["district"] = d
        else:
            problems.append(
                f"District '{args['district']}' is not supported. Available: {', '.join(DISTRICTS)}")

    for key, unit_key, out in [("roof_area", "roof_area_unit", "roof_area_m2"),
                               ("available_area", "available_area_unit", "available_area_m2")]:
        if key in args:
            unit = args.get(unit_key)
            if unit not in UNIT_TO_SQM:
                problems.append(f"Unit missing for {key}. Ask the user: sq ft, sq m or gaj?")
                continue
            sqm = round(args[key] * UNIT_TO_SQM[unit], 1)
            lo, hi = (5, 5000) if key == "roof_area" else (0, 100000)
            if lo <= sqm <= hi:
                profile[out] = sqm
            else:
                problems.append(f"{key} of {sqm} m2 looks unrealistic. Ask the user to confirm.")

    if "people" in args:
        if 1 <= args["people"] <= 100:
            profile["people"] = args["people"]
        else:
            problems.append("Number of people looks unrealistic.")

    for key in ("user_type", "goal", "roof_type", "soil_type"):
        if key in args:
            profile[key] = args[key]

   
    if profile.get("district") and "soil_type" not in profile:
        soil = lookup_soil(profile["district"])
        if soil:
            profile["soil_type"] = soil

    return profile, problems


def missing(profile):
    need = ["district", "user_type", "goal", "available_area_m2"]
    if profile.get("user_type") == "household" or profile.get("goal") == "storage":
        need += ["roof_area_m2", "roof_type", "people"]
    return [s for s in need if profile.get(s) is None]   # 0 counts as answered