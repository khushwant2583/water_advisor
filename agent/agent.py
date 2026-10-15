import json
import ollama
from agent.profile import merge_profile, missing

MODEL = "qwen2.5:7b"
UNITS = ["sqft", "sqm", "sqyd", "gaj"]

# ---------- 1. Tools the model can call ----------
TOOLS = [
    {"type": "function", "function": {
        "name": "update_profile",
        "description": "Save details the user stated or corrected. Include ONLY fields the user "
                       "explicitly mentioned. Never guess. Call it whenever the user gives any detail.",
        "parameters": {"type": "object", "properties": {
            "district": {"type": "string"},
            "user_type": {"type": "string", "enum": ["household", "farmer"]},
            "goal": {"type": "string", "enum": ["storage", "groundwater_recharge", "irrigation"]},
            "roof_area": {"type": "number", "description": "Number exactly as the user said it"},
            "roof_area_unit": {"type": "string", "enum": UNITS, "description": "Only if the user stated a unit"},
            "roof_type": {"type": "string", "enum": ["concrete", "tiles", "metal", "asbestos"],
                          "description": "slab/RCC/pakka = concrete; tin/sheet = metal"},
            "people": {"type": "integer"},
            "available_area": {"type": "number", "description": "Open ground. 0 if the user says none."},
            "available_area_unit": {"type": "string", "enum": UNITS},
            "soil_type": {"type": "string", "enum": ["sandy", "loamy", "clay"]}}}}},
    {"type": "function", "function": {
        "name": "design_system",
        "description": "Run the rainwater design using the saved profile. Takes no arguments. "
                       "Call only when nothing is missing and the user confirmed the summary.",
        "parameters": {"type": "object", "properties": {}}}},
]

# ---------- 2. Instructions for the model (domain + rules) ----------
SYSTEM = """You are a rainwater harvesting advisor for Rajasthan, India.

RULES
- Fill details only from what the user actually said. Never assume or use defaults.
- You MUST call update_profile whenever the user gives or corrects any detail.
- If still_missing is not empty, ask only for those, at most two at a time.
- If the user gives a size without a unit, ask for the unit.
- If update_profile returns problems, explain them simply and ask again.
- Before calling design_system, give a one-line summary and wait for the user to agree.
- Never calculate or invent numbers. Every figure must come from a tool result.
- Reply in the user's language (English, Hindi or Hinglish). Keep answers short.
- This is not an engineering design. Advise a site visit before building.
- Stay on topic. Politely decline unrelated requests.
- If a tool result has "dummy": true, tell the user it is test data.

CURRENT PROFILE (what the user has told us so far):
{profile}
"""

# ---------- 3. Placeholder until your friend's real design function is ready ----------
def design_stub(profile):
    return {"dummy": True, "district": profile["district"],
            "tank_liters": 10000, "annual_harvest_l": 52000,
            "recommendation": "Storage tank (dummy data)"}

# ---------- 4. Run a tool ----------
def clean_args(args):
    """Small models sometimes send numbers as text. Fix that here."""
    out = dict(args)
    for k in ("roof_area", "available_area"):
        if k in out:
            try:
                out[k] = float(out[k])
            except (TypeError, ValueError):
                out.pop(k)
    if "people" in out:
        try:
            out["people"] = int(out["people"])
        except (TypeError, ValueError):
            out.pop("people")
    return out

def run_tool(name, args, profile, store):
    if name == "update_profile":
        _, problems = merge_profile(profile, args)
        return {"saved": profile, "still_missing": missing(profile), "problems": problems}
    if name == "design_system":
        gaps = missing(profile)
        if gaps:
            return {"error": "Cannot design yet", "still_missing": gaps}
        result = design_stub(profile)
        store["design"] = result
        return result
    return {"error": f"unknown tool {name}"}

# ---------- 5. The agent function ----------
def chat_turn(user_text, messages, profile, store):
    messages.append({"role": "user", "content": user_text})
    for _ in range(6):                                   # stop endless loops
        system = SYSTEM.format(profile=json.dumps(profile, ensure_ascii=False, indent=2))
        resp = ollama.chat(model=MODEL,
                           messages=[{"role": "system", "content": system}] + messages,
                           tools=TOOLS)
        msg = resp.message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content or ""

        for call in msg.tool_calls:
            name = call.function.name
            args = clean_args(call.function.arguments)
            print(f"   [tool] {name} {args}")            # log shown in the terminal
            out = run_tool(name, args, profile, store)
            messages.append({"role": "tool", "tool_name": name,
                             "content": json.dumps(out, default=str, ensure_ascii=False)})
    return "Sorry, I got stuck. Please rephrase."