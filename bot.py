from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import csv
import os
import random

TOKEN = "TELEGRAM_BOT_TOKEN"

ADMIN_ID = 8160417866

# Stores support ticket message IDs and user IDs
support_tickets = {}

# Registration states
NAME, EMAIL, PHONE, COUNTRY, WALLET, CHECK_CASE = range(6)

# Refund states
RF_NAME, RF_EMAIL, RF_PHONE, RF_COUNTRY, RF_WALLET, RF_AMOUNT, RF_COIN, RF_DATE, RF_HASH, RF_PROOF, RF_DESCRIPTION = range(100, 111)

# Support state
SUPPORT = 200

menu = [
    ["💬 Chat with Support"],
    ["🆕 New User Registration"],
    ["💰 Submit Refund Request"],
    ["📊 Check Status"],
    ["ℹ️ Help"],
]

cancel_menu = [
    ["❌ Cancel"]
]

cancel_markup = ReplyKeyboardMarkup(
    cancel_menu,
    resize_keyboard=True
)

reply_markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)
async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n/update CASE_ID STATUS\n\nExample:\n/update QNP-123456 Approved"
        )
        return

    case_id = context.args[0]
    new_status = " ".join(context.args[1:])

    rows = []

    with open("refund_requests.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        rows = list(reader)

    updated = False

    for row in rows[1:]:
        if row[0] == case_id:
            row[1] = new_status
            updated = True
            break

    if not updated:
        await update.message.reply_text("❌ Case ID not found.")
        return

    with open("refund_requests.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    await update.message.reply_text(
        f"✅ {case_id} has been updated to: {new_status}"
    )
    
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

    if text == "ℹ️ Help":
        await update.message.reply_text(
            "Use the menu buttons to navigate through the portal."
        )
        
# ==========================
# SUPPORT TICKET SYSTEM
# ==========================

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 Please describe your issue in one message.",
        reply_markup=cancel_markup,
    )
    return SUPPORT


async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🎫 NEW SUPPORT TICKET\n\n"
            f"👤 Name: {user.full_name}\n"
            f"🆔 User ID: {user.id}\n"
            f"📛 Username: @{user.username if user.username else 'None'}\n\n"
            f"💬 Message:\n{update.message.text}"
        )
        )
    
    support_tickets[msg.message_id] = user.id

    await update.message.reply_text(
        "✅ Your message has been sent successfully.\n\n"
        "A support representative will reply shortly.",
        reply_markup=reply_markup,
    )

    return ConversationHandler.END


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    msg_id = update.message.reply_to_message.message_id

    if msg_id not in support_tickets:
        return

    user_id = support_tickets[msg_id]

    await context.bot.send_message(
        chat_id=user_id,
        text=f"💬 Support Reply\n\n{update.message.text}"
    )

    await update.message.reply_text("✅ Reply delivered.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Operation cancelled.\n\nYou have been returned to the main menu.",
        reply_markup=reply_markup,
    )

    return ConversationHandler.END

# ==========================
# REGISTRATION
# ==========================

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👤 Enter your Full Name:",
        reply_markup=cancel_markup,
    )
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

    await update.message.reply_text(
        "You can now use the menu below.",
        reply_markup=reply_markup,
    )

    context.user_data.clear()
    return ConversationHandler.END

# ==========================
# REFUND REQUEST
# ==========================

async def refund_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tx_hashes"] = []

    await update.message.reply_text(
        "👤 Enter your Full Name:",
        reply_markup=cancel_markup,
    )

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

    case_id = f"QNP-{random.randint(100000, 999999)}"
    hashes = "\n".join(context.user_data["tx_hashes"])

    csv_file = "refund_requests.csv"
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    if not file_exists:
        writer.writerow([
            "Case ID",
            "Status",
            "Name",
            "Email",
            "Phone",
            "Country",
            "Wallet",
            "Amount",
            "Coin",
            "Transaction Date",
            "Transaction Hashes",
            "Proof File ID",
            "Description"
        ])

    writer.writerow([
        case_id,
        "Pending",
        context.user_data["rf_name"],
        context.user_data["rf_email"],
        context.user_data["rf_phone"],
        context.user_data["rf_country"],
        context.user_data["rf_wallet"],
        context.user_data["rf_amount"],
        context.user_data["rf_coin"],
        context.user_data["rf_date"],
        hashes,
        context.user_data["proof"],
        context.user_data["description"],
    ])

        await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=context.user_data["proof"],
        caption=(
            f"📥 NEW REFUND REQUEST\n\n"
            f"🆔 Case ID: {case_id}\n"
            f"📌 Status: Pending\n\n"
            f"👤 Name: {context.user_data['rf_name']}\n"
            f"📧 Email: {context.user_data['rf_email']}\n"
            f"📱 Phone: {context.user_data['rf_phone']}\n"
            f"🌍 Country: {context.user_data['rf_country']}\n"
            f"👛 Wallet: {context.user_data['rf_wallet']}\n\n"
            f"💰 Amount Lost: {context.user_data['rf_amount']}\n"
            f"🪙 Coin: {context.user_data['rf_coin']}\n"
            f"📅 Transaction Date: {context.user_data['rf_date']}\n\n"
            f"🔗 Transaction Hashes:\n{hashes}\n\n"
            f"📝 Description:\n{context.user_data['description']}"
        )
    )

    await update.message.reply_text(
    f"""✅ Refund Request Submitted Successfully

📄 Case ID: {case_id}

📌 Status: Pending

Please save your Case ID.

Use 📊 Check Status anytime to track your request.
""",
    reply_markup=reply_markup,
)

    context.user_data.clear()
    return ConversationHandler.END


async def check_status_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 Please enter your Case ID:",
        reply_markup=cancel_markup,
    )
    return CHECK_CASE

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    case_id = update.message.text.strip()

    if not os.path.exists("refund_requests.csv"):
        await update.message.reply_text(
            "❌ No refund requests found.",
            reply_markup=reply_markup,
        )
        return ConversationHandler.END

    with open("refund_requests.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)

        next(reader, None)

        for row in reader:
            if row[0] == case_id:
                await update.message.reply_text(
                    f"📄 Case ID: {row[0]}\n"
                    f"📌 Status: {row[1]}",
                    reply_markup=reply_markup,
                )
                return ConversationHandler.END

    await update.message.reply_text(
        "❌ Case ID not found.",
        reply_markup=reply_markup,
    )

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
   fallbacks=[
    MessageHandler(
        filters.Regex("^❌ Cancel$"),
        cancel,
    )
],

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
    fallbacks=[
    MessageHandler(
        filters.Regex("^❌ Cancel$"),
        cancel,
    )
],
)

check_status_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^📊 Check Status$"), check_status_start)
    ],
    states={
        CHECK_CASE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, check_status)
        ],
    },
    fallbacks=[
    MessageHandler(
        filters.Regex("^❌ Cancel$"),
        cancel,
    )
],
)

support_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex("^💬 Chat with Support$"),
            support_start,
        )
    ],
    states={
        SUPPORT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                support_message,
            )
        ],
    },
    fallbacks=[
    MessageHandler(
        filters.Regex("^❌ Cancel$"),
        cancel,
    )
],
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

app = Application.builder().token(TOKEN).request(request).build()

app.add_handler(registration_handler)
app.add_handler(refund_handler)
app.add_handler(check_status_handler)
app.add_handler(support_handler)

app.add_handler(
    MessageHandler(filters.REPLY & filters.TEXT, admin_reply)
)

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, buttons)
)

app.add_handler(CommandHandler("update", update_status))
app.add_handler(CommandHandler("start", start))

print("✅ Bot is running...")

app.run_polling()
