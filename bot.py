from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import random

import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print("TOKEN FOUND:", TOKEN is not None)
print("TOKEN LENGTH:", len(TOKEN) if TOKEN else 0)

# Registration states
NAME, EMAIL, PHONE, COUNTRY, WALLET = range(5)

# Refund states
RF_NAME, RF_EMAIL, RF_PHONE, RF_COUNTRY, RF_WALLET, RF_AMOUNT, RF_COIN, RF_DATE, RF_HASH, RF_PROOF, RF_DESCRIPTION = range(100, 111)

menu = [
    ["💬 Chat with Support"],
    ["🆕 New User Registration"],
    ["💰 Submit Refund Request"],
    ["📊 Check Status"],
    ["ℹ️ Help"],
]

reply_markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

# ==========================
# START
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Quantro Network Pro BOT.\n\nChoose an option below:",
        reply_markup=reply_markup,
    )

# ==========================
# MENU BUTTONS
# ==========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💬 Chat with Support":
        await update.message.reply_text(
            "A support representative will be available soon."
        )

    elif text == "📊 Check Status":
        await update.message.reply_text(
            "Please enter your Case ID."
        )

    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "Use the menu buttons to navigate through the portal."
        )

# ==========================
# REGISTRATION
# ==========================

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Enter your Full Name:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📧 Enter your Email:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("📱 Enter your Phone Number:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("🌍 Enter your Country:")
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    await update.message.reply_text("👛 Enter your Wallet Address:")
    return WALLET

async def get_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["wallet"] = update.message.text

    await update.message.reply_text(
        f"✅ Registration Complete!\n\n"
        f"👤 {context.user_data['name']}\n"
        f"📧 {context.user_data['email']}\n"
        f"📱 {context.user_data['phone']}\n"
        f"🌍 {context.user_data['country']}\n"
        f"👛 {context.user_data['wallet']}",
        reply_markup=reply_markup,
    )

    context.user_data.clear()
    return ConversationHandler.END

# ==========================
# REFUND REQUEST
# ==========================

async def refund_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tx_hashes"] = []
    await update.message.reply_text("👤 Enter your Full Name:")
    return RF_NAME

async def refund_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rf_name"] = update.message.text
    await update.message.reply_text("📧 Enter your Email:")
    return RF_EMAIL

async def refund_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rf_email"] = update.message.text
    await update.message.reply_text("📱 Enter your Phone Number:")
    return RF_PHONE

async def refund_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rf_phone"] = update.message.text
    await update.message.reply_text("🌍 Enter your Country:")
    return RF_COUNTRY

async def refund_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rf_country"] = update.message.text
    await update.message.reply_text("👛 Enter your Wallet Address:")
    return RF_WALLET

async def refund_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rf_wallet"] = update.message.text
    await update.message.reply_text("💰 Amount Lost:")
    return RF_AMOUNT

async def refund_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rf_amount"] = update.message.text
    await update.message.reply_text("🪙 Cryptocurrency (BTC, ETH, USDT, etc.):")
    return RF_COIN

async def refund_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rf_coin"] = update.message.text
    await update.message.reply_text("📅 Date of Transaction:")
    return RF_DATE

async def refund_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rf_date"] = update.message.text
    await update.message.reply_text(
        "🔗 Enter Transaction Hash #1\n\n(Type DONE when finished or enter up to 5 hashes.)"
    )
    return RF_HASH
# ==========================
# TRANSACTION HASHES
# ==========================

async def refund_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # User finished entering hashes
    if update.message.text.upper() == "DONE":
        if len(context.user_data["tx_hashes"]) == 0:
            await update.message.reply_text(
                "⚠️ Please enter at least one Transaction Hash."
            )
            return RF_HASH

        await update.message.reply_text(
            "📸 Please upload a screenshot or other proof."
        )
        return RF_PROOF

    # Save hash
    context.user_data["tx_hashes"].append(update.message.text)

    total = len(context.user_data["tx_hashes"])

    # Allow up to 5 hashes
    if total < 5:
        await update.message.reply_text(
            f"✅ Transaction Hash #{total} saved.\n\n"
            f"Enter Transaction Hash #{total + 1}\n"
            "or type DONE to continue."
        )
        return RF_HASH

    # Maximum reached
    await update.message.reply_text(
        "✅ Maximum of 5 Transaction Hashes received.\n\n"
        "📸 Please upload a screenshot or other proof."
    )

    return RF_PROOF


# ==========================
# SCREENSHOT / PROOF
# ==========================

async def refund_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.photo:
        context.user_data["proof"] = update.message.photo[-1].file_id

    elif update.message.document:
        context.user_data["proof"] = update.message.document.file_id

    else:
        await update.message.reply_text(
            "⚠️ Please upload a screenshot or document as proof."
        )
        return RF_PROOF

    await update.message.reply_text(
        "📝 Briefly describe what happened:"
    )

    return RF_DESCRIPTION


# ==========================
# FINISH REFUND REQUEST
# ==========================

async def refund_description(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["description"] = update.message.text

    case_id = f"QNP-{random.randint(100000,999999)}"

    hashes = "\n".join(context.user_data["tx_hashes"])

    await update.message.reply_text(
        f"""
✅ Refund Request Submitted Successfully

📄 Case ID:
{case_id}

👤 Name:
{context.user_data['rf_name']}

📧 Email:
{context.user_data['rf_email']}

📱 Phone:
{context.user_data['rf_phone']}

🌍 Country:
{context.user_data['rf_country']}

👛 Wallet:
{context.user_data['rf_wallet']}

💰 Amount Lost:
{context.user_data['rf_amount']}

🪙 Cryptocurrency:
{context.user_data['rf_coin']}

📅 Transaction Date:
{context.user_data['rf_date']}

🔗 Transaction Hashes:
{hashes}

📝 Description:
{context.user_data['description']}

Your refund request has been received successfully.

Please save your Case ID.

Use 📊 Check Status anytime to track your request.
""",
        reply_markup=reply_markup,
    )

    context.user_data.clear()

    return ConversationHandler.END

# ==========================
# REGISTRATION HANDLER
# ==========================

registration_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^🆕 New User Registration$"), register)
    ],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
        WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wallet)],
    },
    fallbacks=[],
)

# ==========================
# REFUND HANDLER
# ==========================

refund_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^💰 Submit Refund Request$"), refund_start)
    ],
    states={
        RF_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_name)],
        RF_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_email)],
        RF_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_phone)],
        RF_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_country)],
        RF_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_wallet)],
        RF_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_amount)],
        RF_COIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_coin)],
        RF_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_date)],
        RF_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_hash)],
        RF_PROOF: [
    MessageHandler(
        filters.PHOTO | filters.Document.ALL,
        refund_proof,
    )
],
        RF_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, refund_description)
        ],
    },
    fallbacks=[],
)

# ==========================
# START APPLICATION
# ==========================

from telegram.request import HTTPXRequest

request = HTTPXRequest(
    connect_timeout=30,
    read_timeout=30,
    write_timeout=30,
    pool_timeout=30,
)
print(TOKEN)
print(type(TOKEN))
app = Application.builder().token(TOKEN).request(request).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(registration_handler)

app.add_handler(refund_handler)

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, buttons)
)

print("✅ Bot is running...")

app.run_polling()
