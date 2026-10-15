import json
import re
import ollama
from rapidfuzz import process, fuzz
from agent.profile import merge_profile, missing, DISTRICTS

MODEL = "qwen2.5:3b"      # run: ollama pull qwen2.5:3b
USE_MODEL = True          # set False to test with rules only (instant)
UNITS = ["sqft", "sqm", "sqyd", "gaj"]

# ================= PART 1: EXTRACTION =================
EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "district": {"type": "string"},
        "user_type": {"type": "string", "enum": ["household", "farmer"]},
        "goal": {"type": "string", "enum": ["storage", "groundwater_recharge", "irrigation"]},
        "roof_area": {"type": "number"},
        "roof_area_unit": {"type": "string", "enum": UNITS},
        "roof_type": {"type": "string", "enum": ["concrete", "tiles", "metal", "asbestos"]},
        "people": {"type": "integer"},
        "available_area": {"type": "number"},
        "available_area_unit": {"type": "string", "enum": UNITS},
    },
}

EXTRACT_PROMPT = """Extract rainwater-project details from the user's message.
Return JSON with ONLY the fields the user explicitly stated. Return {} if none.
Never guess or fill in missing values.
Hints: slab/RCC/pakka = concrete; tin/sheet = metal; khapra = tiles;
ghar/home = household; kheti/farm = farmer; store/tanki = storage.
Messages may be English, Hindi or Hinglish."""

EXAMPLES = [
    ("Jodhpur me kheti hai, tanki banani hai",
     {"district": "Jodhpur", "user_type": "farmer", "goal": "storage"}),
    ("meri chhat 800 sq ft tin ki hai, 4 log rehte hain",
     {"roof_area": 800, "roof_area_unit": "sqft", "roof_type": "metal", "people": 4}),
    ("hello", {}),
]

UNIT_WORDS = {
    "sqft": ["sq ft", "sqft", "sq.ft", "square feet", "square foot", "feet", "ft"],
    "sqm": ["sq m", "sqm", "sq.m", "square meter", "square metre", "meter", "metre"],
    "sqyd": ["sq yd", "sqyd", "yard"],
    "gaj": ["gaj"],
}


def validate_extraction(data, user_text):
    """Drop anything the model invented."""
    text = user_text.lower().replace(",", "")
    out = {}
    for k, v in data.items():
        if v in (None, "", "unknown"):
            continue
        if k in ("roof_area", "available_area", "people"):
            try:
                num = float(v)
            except (TypeError, ValueError):
                continue
            if k == "available_area" and num == 0:
                out["available_area"] = 0
                out["available_area_unit"] = "sqm"
                continue
            if str(int(num)) not in text:             # number must be in the message
                continue
            out[k] = int(num) if k == "people" else num
            continue
        if k in ("roof_area_unit", "available_area_unit"):
            if k == "available_area_unit" and out.get("available_area") == 0:
                continue
            if any(w in text for w in UNIT_WORDS.get(v, [])):
                out[k] = v                            # keep a unit only if the user said it
            continue
        out[k] = v
    return out


# ---- rule-based extractor: instant, no model needed ----
UNIT_REGEX = (r"(sq\.?\s?ft|sqft|square\s?f(?:ee|oo)t|sq\.?\s?m|sqm|"
              r"square\s?met(?:er|re)s?|sq\.?\s?yd|gaj)")


def unit_from_text(u):
    u = u.lower().replace(" ", "").replace(".", "")
    if "yd" in u:
        return "sqyd"
    if "gaj" in u:
        return "gaj"
    if "ft" in u or "feet" in u or "foot" in u:
        return "sqft"
    return "sqm"


def rule_extract(text):
    t = text.lower()
    out = {}

    # district: fuzzy-match each word against your district list
    for word in re.findall(r"[a-z]{4,}", t):
        m = process.extractOne(word.title(), DISTRICTS, scorer=fuzz.ratio, score_cutoff=80)
        if m:
            out["district"] = m[0]
            break

    # areas: number + unit; "khuli/open/zameen" nearby means open ground, else roof
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*" + UNIT_REGEX, t):
        before = t[max(0, m.start() - 25):m.start()]
        key = "available_area" if re.search(r"khuli|open|zameen|jagah|plot|land", before) else "roof_area"
        out[key] = float(m.group(1))
        out[key + "_unit"] = unit_from_text(m.group(2))

    # "no open land" is a valid answer: 0
    if re.search(r"(khuli|open)[a-z ]{0,12}(nahi|nahin|nhi|no\b|none)|no open|no land|jagah nahi", t):
        out["available_area"] = 0
        out["available_area_unit"] = "sqm"

    p = re.search(r"(\d+)\s*(log|people|persons|members|sadasya)", t)
    if p:
        out["people"] = int(p.group(1))

    if re.search(r"\b(slab|rcc|pakka|concrete|cement)\b", t):
        out["roof_type"] = "concrete"
    elif re.search(r"\b(tin|sheet|metal|dhatu)\b", t):
        out["roof_type"] = "metal"
    elif re.search(r"\b(tile|tiles|khapra|khaprail)\b", t):
        out["roof_type"] = "tiles"
    elif re.search(r"\basbestos\b", t):
        out["roof_type"] = "asbestos"

    if re.search(r"\b(kheti|khet|farm|farmer|farming|kisan)\b", t):
        out["user_type"] = "farmer"
    elif re.search(r"\b(ghar|home|house|household|domestic)\b", t):
        out["user_type"] = "household"

    if re.search(r"\b(recharge|groundwater|borewell|bore)\b", t):
        out["goal"] = "groundwater_recharge"
    elif re.search(r"\b(irrigation|sinchai|sinchayi)\b", t):
        out["goal"] = "irrigation"
    elif re.search(r"\b(store|storage|tank|tanki)\b", t):
        out["goal"] = "storage"

    return out


def extract_details(user_text):
    rules = rule_extract(user_text)
    model = {}
    if USE_MODEL:
        messages = [{"role": "system", "content": EXTRACT_PROMPT}]
        for q, a in EXAMPLES:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": json.dumps(a)})
        messages.append({"role": "user", "content": user_text})
        resp = ollama.chat(model=MODEL, messages=messages, format=EXTRACT_SCHEMA,
                           options={"temperature": 0, "num_predict": 150})
        raw = resp.message.content
        print(f"   [model output] {raw}")                   # debug line
        try:
            model = validate_extraction(json.loads(raw), user_text)
        except json.JSONDecodeError:
            model = {}
        # reject a district the model made up (its first letters must be in the text)
        if "district" in model and model["district"].lower()[:4] not in user_text.lower():
            model.pop("district")
    print(f"   [rules]        {rules}")
    return {**model, **rules}                               # rules win when both find a value


# ================= PART 2: REPLIES WRITTEN BY PYTHON =================
QUESTIONS = {
    "hinglish": {
        "district": "Aap kis district me rehte hain?",
        "user_type": "Kya ye ghar ke liye hai ya kheti (farmer) ke liye?",
        "goal": "Aap paani store karna chahte hain, zameen me recharge karna, ya sinchai ke liye?",
        "available_area_m2": "Aapke paas khuli zameen kitni hai? (nahi hai to 'nahi' likhein)",
        "roof_area_m2": "Chhat kitni badi hai? (unit ke saath, jaise 1200 sq ft)",
        "roof_type": "Chhat kis type ki hai: concrete (slab), tin, ya tiles?",
        "people": "Ghar me kitne log hain?",
    },
    "english": {
        "district": "Which district are you in?",
        "user_type": "Is this for a household or for farming?",
        "goal": "Do you want to store water, recharge groundwater, or use it for irrigation?",
        "available_area_m2": "How much open ground do you have? (say 'none' if there is none)",
        "roof_area_m2": "How big is your roof? (with a unit, e.g. 1200 sq ft)",
        "roof_type": "What is the roof made of: concrete, metal sheet, or tiles?",
        "people": "How many people live in the house?",
    },
}

HINGLISH_WORDS = ["hai", "hain", "me", "mein", "nahi", "chhat", "log", "karna", "kya",
                  "ghar", "kheti", "paani", "aap", "mera", "meri"]


def detect_language(text):
    if any(2304 <= ord(c) <= 2431 for c in text):           # Devanagari script
        return "hinglish"
    words = text.lower().split()
    return "hinglish" if any(w in words for w in HINGLISH_WORDS) else "english"


def summary_line(profile):
    parts = []
    if profile.get("district"):
        parts.append(profile["district"])
    if profile.get("roof_area_m2") is not None:
        parts.append(f"roof {profile['roof_area_m2']} m2")
    if profile.get("roof_type"):
        parts.append(profile["roof_type"])
    if profile.get("people"):
        parts.append(f"{profile['people']} people")
    return ", ".join(parts)


def build_reply(lang, profile, gaps, problems, design):
    if problems:
        return "Please check: " + " ".join(problems)

    heard = summary_line(profile)
    if gaps:
        asks = [QUESTIONS[lang][g] for g in gaps[:2] if g in QUESTIONS[lang]]
        start = ""
        if heard:
            start = ("Samajh gaya: " if lang == "hinglish" else "Got it: ") + heard + ". "
        return start + " ".join(asks)

    return (f"All details collected ({heard}). "
            f"Recommendation: {design['recommendation']}. "
            f"Estimated yearly harvest: {design['annual_harvest_l']} L, "
            f"suggested tank: {design['tank_liters']} L. "
            + ("(This is test data.) " if design.get("dummy") else "")
            + "These are estimates, so please get a site visit before building.")


def design_stub(profile):
    """DUMMY. Replace with your friend's real design_system later."""
    return {"dummy": True, "district": profile["district"],
            "tank_liters": 10000, "annual_harvest_l": 52000,
            "recommendation": "Storage tank (dummy data)"}


# ================= PART 3: ONE CHAT TURN =================
def chat_turn(user_text, messages, profile, store):
    details = extract_details(user_text)
    print(f"   [extracted]    {details}")
    lang = detect_language(user_text)

    # nothing understood and nothing saved yet: greet and redirect
    if not details and not profile:
        reply = ("Main rainwater harvesting me madad karta hoon. Apna district, chhat ka size "
                 "aur kitne log hain, bataiye." if lang == "hinglish" else
                 "I help with rainwater harvesting. Tell me your district, roof size "
                 "and how many people live there.")
        messages.append({"role": "user", "content": user_text})
        messages.append({"role": "assistant", "content": reply})
        return reply

    _, problems = merge_profile(profile, details)
    gaps = missing(profile)

    design = None
    if profile and not gaps:
        design = design_stub(profile)
        store["design"] = design

    reply = build_reply(lang, profile, gaps, problems, design)
    messages.append({"role": "user", "content": user_text})
    messages.append({"role": "assistant", "content": reply})
    return reply