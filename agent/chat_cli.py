from agent.brain import chat_turn

messages, profile, store = [], {}, {}
print("Rainwater Harvesting Advisor (type 'quit' to exit)\n")
while True:
    text = input("You: ").strip()
    if text.lower() in ("quit", "exit"):
        break
    print("Bot:", chat_turn(text, messages, profile, store), "\n")