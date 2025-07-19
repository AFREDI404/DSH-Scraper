import os
import logging
import random
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask
from threading import Thread

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Function to keep the bot alive 24/7 on Replit
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Helper Functions ---

# Checks if a card number is valid using the Luhn algorithm
def is_luhn_valid(card_number):
    try:
        num_digits = len(card_number)
        s = 0
        is_second = False
        for i in range(num_digits - 1, -1, -1):
            d = int(card_number[i])
            if is_second:
                d = d * 2
            s += d // 10
            s += d % 10
            is_second = not is_second
        return s % 10 == 0
    except (ValueError, TypeError):
        return False

# Generates a valid card number from a BIN
def generate_card(bin_number, month=None, year=None, cvv=None):
    card_number = bin_number + ''.join(random.choices('0123456789', k=15 - len(bin_number)))
    for i in range(10):
        temp_card = card_number + str(i)
        if is_luhn_valid(temp_card):
            card_number = temp_card
            break
    exp_month = month if month and month.isdigit() and 1 <= int(month) <= 12 else f"{random.randint(1, 12):02d}"
    exp_year = year if year and year.isdigit() and len(year) == 2 else str(random.randint(25, 30))
    gen_cvv = cvv if cvv and cvv.isdigit() else f"{random.randint(100, 999):03d}"
    return f"{card_number}|{exp_month}|{exp_year}|{gen_cvv}"

# Gets information about a BIN
def get_bin_info(bin_number):
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_number[:6]}")
        if response.status_code == 200:
            data = response.json()
            bank_name = data.get('bank', {}).get('name', 'N/A')
            country = data.get('country', {}).get('name', 'N/A')
            card_type = data.get('type', 'N/A').capitalize()
            scheme = data.get('scheme', 'N/A').capitalize()
            return f"🔹 **Issuer:** {bank_name}\n🔹 **Country:** {country}\n🔹 **Type:** {card_type}\n🔹 **Scheme:** {scheme}"
        else:
            return "🔹 BIN Information not found."
    except Exception:
        return "🔹 Error fetching BIN information."

# --- Command Handlers ---

def start(update: Update, context: CallbackContext) -> None:
    user_name = update.effective_user.first_name
    welcome_message = (
        f"Hi {user_name}! 👋\n\n"
        "I am an advanced automation bot with many tools.\n"
        "Use /help to see the list of all available commands."
    )
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
    **Here are the available commands:**

    💳 **Card Generation & Check:**
    `/gen <BIN> [MM] [YY]` - Generates 10 credit cards from a BIN.
    `/bin <BIN>` - Checks information of a BIN.
    `/check <CARD_NUMBER>` - Validates a credit card number.
    `/rand` - Generates a random credit card.

    👤 **Information Tools:**
    `/fakeinfo [country_code]` - Generates a fake identity. (e.g., `/fakeinfo US`)
    `/myinfo` - Shows your Telegram user info.

    🌐 **Network Tools:**
    `/proxy <IP:PORT>` - Checks if a proxy is working.

    ℹ️ **Bot Info:**
    `/help` - Shows this help message.
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

def gen_command(update: Update, context: CallbackContext) -> None:
    args = context.args
    if not args or not args[0].isdigit() or len(args[0]) < 6:
        update.message.reply_text("❌ Please provide a valid BIN (at least 6 digits).\nExample: `/gen 457382`")
        return

    bin_number = args[0]
    month = args[1] if len(args) > 1 else None
    year = args[2] if len(args) > 2 else None

    msg = update.message.reply_text("⏳ Generating cards, please wait...")

    cards = [generate_card(bin_number, month, year) for _ in range(10)]
    bin_info = get_bin_info(bin_number)

    generated_cards_text = "\n".join([f"`{card}`" for card in cards])

    response_message = f"🔴 **Generated Cards:**\n{generated_cards_text}\n\n{bin_info}"
    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text=response_message, parse_mode='Markdown')

def bin_command(update: Update, context: CallbackContext) -> None:
    if not context.args or not context.args[0].isdigit() or len(context.args[0]) < 6:
        update.message.reply_text("❌ Please provide a valid BIN (at least 6 digits).\nExample: `/bin 457382`")
        return
    bin_info = get_bin_info(context.args[0])
    update.message.reply_text(bin_info, parse_mode='Markdown')

def check_command(update: Update, context: CallbackContext) -> None:
    if not context.args or not context.args[0].isdigit():
        update.message.reply_text("❌ Please provide a valid card number to check.")
        return
    card_number = context.args[0]
    if is_luhn_valid(card_number):
        response = f"✅ **Valid:** The card number `{card_number}` is valid according to the Luhn algorithm."
    else:
        response = f"❌ **Invalid:** The card number `{card_number}` is not valid."
    update.message.reply_text(response, parse_mode='Markdown')

def rand_command(update: Update, context: CallbackContext) -> None:
    common_bins = ["457382", "536418", "491267", "549618", "426285", "378282"]
    random_bin = random.choice(common_bins)
    card = generate_card(random_bin)
    bin_info = get_bin_info(random_bin)
    response = f"🔴 **Generated Card:**\n`{card}`\n\n{bin_info}"
    update.message.reply_text(response, parse_mode='Markdown')

def myinfo_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    info_text = (
        f"👤 **Your Info:**\n\n"
        f"🔹 **First Name:** {user.first_name}\n"
        f"🔹 **User ID:** `{user.id}`\n"
        f"🔹 **Username:** @{user.username if user.username else 'N/A'}"
    )
    update.message.reply_text(info_text, parse_mode='Markdown')

def proxy_command(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text("❌ Please provide a proxy.\nExample: `/proxy 1.1.1.1:8080`")
        return
    proxy = context.args[0]
    proxies = {'http': f'http://{proxy}', 'https': f'https://{proxy}'}
    msg = update.message.reply_text(f"⏳ Checking proxy `{proxy}`...")
    try:
        response = requests.get("http://www.google.com", proxies=proxies, timeout=5)
        if response.status_code == 200:
            result = f"✅ **Live:** The proxy `{proxy}` is working!"
        else:
            result = f"❌ **Dead:** The proxy `{proxy}` returned status code {response.status_code}."
    except requests.exceptions.RequestException:
        result = f"❌ **Dead:** The proxy `{proxy}` failed to connect."
    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text=result, parse_mode='Markdown')

def fakeinfo_command(update: Update, context: CallbackContext) -> None:
    country_code = context.args[0].upper() if context.args else random.choice(['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'IN', 'BR'])
    msg = update.message.reply_text(f"⏳ Generating fake info for {country_code}...")
    try:
        response = requests.get(f"https://randomuser.me/api/?nat={country_code}")
        if response.status_code == 200 and response.json()['results']:
            user = response.json()['results'][0]
            name = f"{user['name']['first']} {user['name']['last']}"
            location = user['location']
            address = f"{location['street']['number']} {location['street']['name']}, {location['city']}, {location['state']}, {location['postcode']}"
            country = location['country']
            email = user['email']
            phone = user['phone']

            info_text = (
                f"👤 **Generated Fake Identity ({country})**\n\n"
                f"🔹 **Name:** {name}\n"
                f"🔹 **Address:** {address}\n"
                f"🔹 **Email:** {email}\n"
                f"🔹 **Phone:** {phone}"
            )
        else:
            info_text = "❌ Could not generate info. The country code might be invalid. Try common codes like US, GB, IN, etc."
    except Exception:
        info_text = "❌ An error occurred while fetching data."
    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text=info_text, parse_mode='Markdown')

def main() -> None:
    # Get token from secrets
    token = os.environ.get('BOT_TOKEN')
    if not token:
        print("Error: BOT_TOKEN not found in secrets!")
        return

    updater = Updater(token)
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("gen", gen_command))
    dispatcher.add_handler(CommandHandler("bin", bin_command))
    dispatcher.add_handler(CommandHandler("check", check_command))
    dispatcher.add_handler(CommandHandler("rand", rand_command))
    dispatcher.add_handler(CommandHandler("myinfo", myinfo_command))
    dispatcher.add_handler(CommandHandler("proxy", proxy_command))
    dispatcher.add_handler(CommandHandler("fakeinfo", fakeinfo_command))

    # Keep the bot alive
    keep_alive()

    # Start the Bot
    updater.start_polling()
    print("Bot is running with all new features!")
    updater.idle()

if __name__ == '__main__':
    main()
