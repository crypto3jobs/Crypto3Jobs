import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set your bot token and Stripe API key
BOT_TOKEN = os.getenv('BOT_TOKEN')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = STRIPE_SECRET_KEY

bot = telebot.TeleBot(BOT_TOKEN)
bot.user_data = {}  # Temporary data storage for users

# Pricing structure
base_price = 199
featured_price = 149

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    keyboard = InlineKeyboardMarkup()
    keyboard.row_width = 2
    keyboard.add(
        InlineKeyboardButton("Search Jobs", callback_data="search_jobs"),
        InlineKeyboardButton("Post a Job", callback_data="post_job"),
        InlineKeyboardButton("Help", callback_data="help")
    )
    bot.send_message(chat_id, "Welcome to Crypto3Jobs Bot!\n\nSelect an option below:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "post_job")
def choose_featured(call):
    chat_id = call.message.chat.id
    bot.user_data[chat_id] = {"featured": False}
    
    explanation = (
        "\U0001F4A1 **Job Post Pricing**:\n"
        f"- Standard Job Post: ${base_price}\n"     
        "\n\U0001F4A1 **Featured Listing Explanation**:\n"
        "- Top Placement: Your job will appear at the top of the job board.\n"
        "- Telegram Alerts: Instant alerts sent to job seekers for 7 days.\n"
        "- View Counter: Track how many people viewed your job post.\n"
        f"\n\nFeatured Listing Cost: ${featured_price} additional."
    )

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(f"Standard Post (${base_price})", callback_data="standard_post"),
        InlineKeyboardButton(f"Featured Post (${base_price + featured_price})", callback_data="featured_post")
    )
    bot.send_message(chat_id, explanation, parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ["standard_post", "featured_post"])
def confirm_payment(call):
    chat_id = call.message.chat.id
    is_featured = call.data == "featured_post"
    bot.user_data[chat_id]["featured"] = is_featured
    
    total_price = base_price
    if is_featured:
        total_price += featured_price
    
    bot.user_data[chat_id]["total_price"] = total_price
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Pay in USD (via Stripe)", callback_data="pay_usd"),
        InlineKeyboardButton("Pay in Crypto", callback_data="pay_crypto")
    )
    bot.send_message(chat_id, f"Total Price: ${total_price:.2f}\n\nSelect your payment method:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "pay_usd")
def process_payment_usd(call):
    chat_id = call.message.chat.id
    total_price = bot.user_data[chat_id]["total_price"]
    
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Crypto3Jobs - Job Listing",
                },
                "unit_amount": int(total_price * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="https://t.me/your_bot?start=payment_success",
        cancel_url="https://t.me/your_bot?start=payment_cancel",
    )
    
    bot.send_message(chat_id, f"Click here to pay: {session.url}")

@bot.callback_query_handler(func=lambda call: call.data == "pay_crypto")
def process_payment_crypto(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "To pay with crypto, please send the total amount to the following wallet address:\n\n*YourCryptoWalletAddressHere*\n\nOnce payment is made, send the transaction ID here for confirmation.", parse_mode="Markdown")

bot.polling(none_stop=True)
