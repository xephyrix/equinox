import os
import requests
from sympy import sympify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from flask import Flask
import threading

# === Load environment variables ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# === Flask app for uptime pings ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# === Get crypto price ===
def get_crypto_price(symbol):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
        r = requests.get(url)
        data = r.json()
        if symbol in data:
            return f"${data[symbol]['usd']}"
    except:
        pass
    return "Error fetching price."

# === Calculator ===
def try_calculate(expression):
    try:
        expr = sympify(expression)
        return str(expr.evalf())
    except:
        return None

# === ChatGPT-style AI ===
def ai_reply(prompt):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
        r = requests.post(url, headers=headers, json=data)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "Error: Could not get AI reply."

# === /ask command ===
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /ask <question>")
        return
    await update.message.reply_text(ai_reply(query))

# === Main message handler ===
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # 1️⃣ Calculation
    result = try_calculate(text)
    if result is not None:
        await update.message.reply_text(f"📐 Result: {result}")
        return

    # 2️⃣ Crypto Price
    if text.lower().startswith("price "):
        coin = text.split("price ")[1].strip()
        price = get_crypto_price(coin)
        await update.message.reply_text(f"💰 {coin.upper()} Price: {price}")
        return

    # 3️⃣ AI Chat
    await update.message.reply_text(ai_reply(text))

# === Run bot ===
def run_bot():
    app_telegram = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app_telegram.add_handler(CommandHandler("ask", ask_command))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    print("🤖 Bot is running...")
    app_telegram.run_polling()

# === Start Flask + Bot ===
threading.Thread(target=run_flask).start()
run_bot()