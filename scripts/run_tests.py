import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.brain import chat_turn

TESTS = [
    ["Jalore me ghar hai, chhat 1200 sq ft slab wali"],
    ["my roof is 1200 in Jodhpur"],                                    # unit missing
    ["tell me a joke"],                                                # off topic
    ["Mumbai me ghar hai"],                                            # unsupported district
    ["Jalore, household, storage, 1200 sq ft concrete roof, 5 people, no open land",
     "yes"],                                                           # full flow
    ["Jalore me hu", "actually Jodhpur"],                              # correction
]

for i, conversation in enumerate(TESTS, 1):
    print(f"\n===== TEST {i} =====")
    messages, profile, store = [], {}, {}
    for text in conversation:
        print("You:", text)
        print("Bot:", chat_turn(text, messages, profile, store))
    print("Profile:", profile)