import ollama

MODEL = "qwen2.5:7b"
SYSTEM = "You are a helpful assistant."

def agent(user_message, history):
    history.append({"role": "user", "content": user_message})
    resp = ollama.chat(model=MODEL,
                       messages=[{"role": "system", "content": SYSTEM}] + history)
    reply = resp.message.content
    history.append({"role": "assistant", "content": reply})
    return reply

history = []
while True:
    text = input("You: ")
    if text.lower() == "quit":
        break
    print("Bot:", agent(text, history), "\n")