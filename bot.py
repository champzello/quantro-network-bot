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
import threading

from flask import Flask

TOKEN = "7864833225:AAFqQnSGjnW_wq7ZDmHYzJU9iKrepg9fgHo"

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
    ["💼 Wallet"],
    ["📈 Investment Plans"],
    ["👥 Referrals"],
    ["🪪 KYC Status"],
    ["💰 Submit Refund Request"],
    ["📊 Check Status"],
    ["💬 Chat with Support"],
    ["📋 My Profile"],
    ["ℹ️ Help"],
]

registration_menu = [
    ["🆕 New User Registration"]
]

registration_markup = ReplyKeyboardMarkup(
    registration_menu,
    resize_keyboard=True
)

cancel_menu = [
    ["🏠 Main Menu"],
    ["❌ Cancel"]
]

cancel_markup = ReplyKeyboardMarkup(
    cancel_menu,
    resize_keyboard=True
)

reply_markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

wallet_menu = [
    ["💳 Quantro Network Wallet"],
    ["🤝 Affiliate Earnings Wallet"],
    ["💵 Fund Wallet"],
    ["💸 Withdraw"],
    ["📜 Transactions"],
    ["⬅️ Back to Main Menu"],
]
wallet_markup = ReplyKeyboardMarkup(wallet_menu, resize_keyboard=True)

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
    

def get_qwallet(uid):
    f="wallets.csv"
    import csv,os
    if not os.path.exists(f):
        with open(f,"w",newline="",encoding="utf-8") as h:
            csv.writer(h).writerow(["User ID","Quantro"])
    rows=list(csv.reader(open(f,encoding="utf-8")))
    for r in rows[1:]:
        if r and r[0]==str(uid): return float(r[1])
    with open(f,"a",newline="",encoding="utf-8") as h:
        csv.writer(h).writerow([uid,"0.00"])
    return 0.0
def set_qwallet(uid,b):
    import csv,os
    f="wallets.csv"
    if not os.path.exists(f):
        open(f,"w").write("User ID,Quantro\n")
    rows=list(csv.reader(open(f,encoding="utf-8")))
    out=[rows[0]];found=False
    for r in rows[1:]:
        if r and r[0]==str(uid):
            r[1]=f"{b:.2f}";found=True
        out.append(r)
    if not found: out.append([uid,f"{b:.2f}"])
    csv.writer(open(f,"w",newline="",encoding="utf-8")).writerows(out)

def log_wallet_transaction(uid,action,amount,balance):
    import csv,os,datetime
    f="wallet_transactions.csv"
    exists=os.path.exists(f)
    with open(f,"a",newline="",encoding="utf-8") as h:
        w=csv.writer(h)
        if not exists:
            w.writerow(["User ID","Action","Amount","Balance","Timestamp"])
        w.writerow([uid,action,f"{amount:.2f}",f"{balance:.2f}",datetime.datetime.now().isoformat()])


async def wallethistory(update,context):
    if update.effective_user.id!=ADMIN_ID:
        return
    if len(context.args)!=1:
        await update.message.reply_text("Usage: /wallethistory USER_ID");return
    uid=context.args[0]
    import csv,os
    f="wallet_transactions.csv"
    if not os.path.exists(f):
        await update.message.reply_text("No transactions.");return
    lines=[]
    with open(f,encoding="utf-8") as h:
        r=csv.reader(h);next(r,None)
        for row in r:
            if row and row[0]==uid:
                lines.append(f"{row[1]} ${row[2]} -> ${row[3]}\n{row[4]}")
    await update.message.reply_text("\n\n".join(lines) if lines else "No transactions for this user.")

async def addbalance(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid,amt=context.args;bal=get_qwallet(uid)+float(amt);set_qwallet(uid,bal);log_wallet_transaction(uid,'Debit',float(amt),bal);log_wallet_transaction(uid,'Credit',float(amt),bal)
    await context.bot.send_message(chat_id=int(uid),text=f"💳 Your Quantro Network Wallet has been credited.\nAmount Added: ${float(amt):.2f}\nNew Balance: ${bal:.2f}")
    await update.message.reply_text(f"✅ Added ${float(amt):.2f} to {uid}. New balance: ${bal:.2f}")
async def subbalance(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid,amt=context.args;bal=max(0,get_qwallet(uid)-float(amt));set_qwallet(uid,bal)
    await context.bot.send_message(chat_id=int(uid),text=f"💳 Your Quantro Network Wallet has been credited.\nAmount Added: ${float(amt):.2f}\nNew Balance: ${bal:.2f}")
    await update.message.reply_text(f"✅ Added ${float(amt):.2f} to {uid}. New balance: ${bal:.2f}")



def get_affiliate_wallet(uid):
    import csv, os
    f="affiliate_wallets.csv"
    if not os.path.exists(f):
        with open(f,"w",newline="",encoding="utf-8") as h:
            csv.writer(h).writerow(["User ID","Affiliate"])
    rows=list(csv.reader(open(f,encoding="utf-8")))
    for r in rows[1:]:
        if r and r[0]==str(uid):
            return float(r[1])
    with open(f,"a",newline="",encoding="utf-8") as h:
        csv.writer(h).writerow([uid,"0.00"])
    return 0.0

def set_affiliate_wallet(uid,balance):
    import csv, os
    f="affiliate_wallets.csv"
    if not os.path.exists(f):
        with open(f,"w",newline="",encoding="utf-8") as h:
            csv.writer(h).writerow(["User ID","Affiliate"])
    rows=list(csv.reader(open(f,encoding="utf-8")))
    out=[rows[0]]
    found=False
    for r in rows[1:]:
        if r and r[0]==str(uid):
            r[1]=f"{balance:.2f}"
            found=True
        out.append(r)
    if not found:
        out.append([uid,f"{balance:.2f}"])
    csv.writer(open(f,"w",newline="",encoding="utf-8")).writerows(out)

def log_affiliate(uid,action,amount,balance):
    import csv,os,datetime
    f="affiliate_transactions.csv"
    exists=os.path.exists(f)
    with open(f,"a",newline="",encoding="utf-8") as h:
        w=csv.writer(h)
        if not exists:
            w.writerow(["User ID","Action","Amount","Balance","Timestamp"])
        w.writerow([uid,action,f"{amount:.2f}",f"{balance:.2f}",datetime.datetime.now().isoformat()])

async def addaffiliate(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid,amt=context.args
    bal=get_affiliate_wallet(uid)+float(amt)
    set_affiliate_wallet(uid,bal)
    log_affiliate(uid,"Credit",float(amt),bal)
    await context.bot.send_message(chat_id=int(uid),text=f"🤝 Affiliate Wallet credited\n+${float(amt):.2f}\nBalance: ${bal:.2f}")
    await update.message.reply_text("Affiliate balance updated.")

async def subaffiliate(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid,amt=context.args
    bal=max(0,get_affiliate_wallet(uid)-float(amt))
    set_affiliate_wallet(uid,bal)
    log_affiliate(uid,"Debit",float(amt),bal)
    await context.bot.send_message(chat_id=int(uid),text=f"🤝 Affiliate Wallet debited\n-${float(amt):.2f}\nBalance: ${bal:.2f}")
    await update.message.reply_text("Affiliate balance updated.")

async def affiliatehistory(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid=context.args[0]
    import csv,os
    f="affiliate_transactions.csv"
    if not os.path.exists(f):
        await update.message.reply_text("No records.");return
    lines=[]
    with open(f,encoding="utf-8") as h:
        r=csv.reader(h);next(r,None)
        for row in r:
            if row and row[0]==uid:
                lines.append(f"{row[1]} ${row[2]} -> ${row[3]}\n{row[4]}")
    await update.message.reply_text("\n\n".join(lines) if lines else "No records.")

# ==========================
# START
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    registered = False

    if os.path.exists("registered_users.csv"):
        with open("registered_users.csv", "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if row and row[0] == user_id:
                    registered = True
                    break

    if registered:
        await update.message.reply_text(
            "👋 Welcome back to Quantro Network Pro BOT.\n\nChoose an option below:",
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            "👋 Welcome to Quantro Network Pro BOT.\n\n"
            "Please complete registration first:",
            reply_markup=registration_markup,
        )

# ==========================
# MENU BUTTONS
# ==========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Ignore buttons handled elsewhere
    if text in (
        "🆕 New User Registration",
        "💰 Submit Refund Request",
        "📊 Check Status",
        "💬 Chat with Support",
        "📋 My Profile",
        "❌ Cancel",
    ):
        return

    if text=="💼 Wallet":
        await update.message.reply_text("💼 Wallet Menu", reply_markup=wallet_markup)
        return
    if text=="⬅️ Back to Main Menu":
        await update.message.reply_text("🏠 Main Menu", reply_markup=reply_markup)
        return
    if text in ("💳 Quantro Network Wallet","🤝 Affiliate Earnings Wallet","💵 Fund Wallet","💸 Withdraw","📜 Transactions","📈 Investment Plans","👥 Referrals","🪪 KYC Status"):
        await update.message.reply_text(f"💳 Quantro Network Wallet\nBalance: ${get_qwallet(update.effective_user.id):.2f}")
        return

    if text == "📋 My Profile":
        user_id=str(update.effective_user.id)
        if os.path.exists("registered_users.csv"):
            with open("registered_users.csv","r",encoding="utf-8") as f:
                r=csv.reader(f); next(r,None)
                for row in r:
                    if row and row[0]==user_id:
                        await update.message.reply_text(f"👤 Name: {row[1]}\n📧 Email: {row[2]}\n📱 Phone: {row[3]}\n🌍 Country: {row[4]}\n👛 Wallet: {row[5]}")
                        return
        await update.message.reply_text("❌ No profile found. Please register first.")
        return

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
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)

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

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🏠 Main Menu\n\nChoose an option below:", reply_markup=reply_markup)
    return ConversationHandler.END

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
    user_id = str(update.effective_user.id)
    context.user_data["user_id"] = user_id
    if os.path.exists("registered_users.csv"):
        with open("registered_users.csv","r",encoding="utf-8") as file:
            reader=csv.reader(file)
            next(reader,None)
            for row in reader:
                if row and row[0]==user_id:
                    await update.message.reply_text(
                        "✅ You have already completed registration.\n\nYou have been returned to the main menu. Choose an option below:",
                        reply_markup=reply_markup,
                    )
                    context.user_data.clear()
                    return ConversationHandler.END

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

    if os.path.exists("registered_users.csv"):
        with open("registered_users.csv","r",encoding="utf-8") as f:
            r=csv.reader(f)
            next(r,None)
            for row in r:
                if len(row)>=6:
                    if row[2].strip().lower()==context.user_data["email"].strip().lower():
                        await update.message.reply_text("❌ This email has already been registered.", reply_markup=reply_markup)
                        return ConversationHandler.END
                    if row[5].strip()==context.user_data["wallet"].strip():
                        await update.message.reply_text("❌ This wallet address has already been registered.", reply_markup=reply_markup)
                        return ConversationHandler.END

    file_exists=os.path.exists("registered_users.csv")
    with open("registered_users.csv","a",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        if not file_exists:
            w.writerow(["User ID","Name","Email","Phone","Country","Wallet"])
        w.writerow([context.user_data["user_id"],context.user_data["name"],context.user_data["email"],context.user_data["phone"],context.user_data["country"],context.user_data["wallet"]])


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

    user_id=str(update.effective_user.id)
    if os.path.exists("registered_users.csv"):
        with open("registered_users.csv","r",encoding="utf-8") as f:
            r=csv.reader(f)
            next(r,None)
            for row in r:
                if row and row[0]==user_id:
                    context.user_data["rf_name"]=row[1]
                    context.user_data["rf_email"]=row[2]
                    context.user_data["rf_phone"]=row[3]
                    context.user_data["rf_country"]=row[4]
                    context.user_data["rf_wallet"]=row[5]
                    await update.message.reply_text("💰 Amount Lost:",reply_markup=cancel_markup)
                    return RF_AMOUNT

    await update.message.reply_text(
        "❌ You must complete registration before submitting a refund request.\n\nPlease select 🆕 New User Registration from the main menu.",
        reply_markup=reply_markup,
    )
    return ConversationHandler.END

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

    hashes = "\n".join(context.user_data["tx_hashes"])

    csv_file = "refund_requests.csv"

    existing_ids = set()
    if os.path.isfile(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    existing_ids.add(row[0])

    while True:
        case_id = f"QNP-{random.randint(100000, 999999)}"
        if case_id not in existing_ids:
            break
    file_exists = os.path.isfile(csv_file)

    if file_exists:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            new_hashes = {h.strip() for h in context.user_data["tx_hashes"]}
            for row in reader:
                if len(row) < 13:
                    continue
                if (row[3].strip().lower()==context.user_data["rf_email"].strip().lower()
                    and row[6].strip()==context.user_data["rf_wallet"].strip()):
                    old_hashes={h.strip() for h in row[10].splitlines() if h.strip()}
                    if new_hashes & old_hashes:
                        await update.message.reply_text("❌ This refund request has already been submitted. If you believe this is an error, contact Support.", reply_markup=reply_markup)
                        context.user_data.clear()
                        return ConversationHandler.END

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
                "Description",
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
        ),
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
        NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ Cancel$"), get_name)],
        EMAIL:[MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ Cancel$"), get_email)],
        PHONE:[MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ Cancel$"), get_phone)],
        COUNTRY:[MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ Cancel$"), get_country)],
        WALLET:[MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ Cancel$"), get_wallet)],
    },
    fallbacks=[
        MessageHandler(filters.Regex("^🏠 Main Menu$"), main_menu),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel),
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
        RF_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_name)],
        RF_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_email)],
        RF_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_phone)],
        RF_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_country)],
        RF_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_wallet)],
        RF_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_amount)],
        RF_COIN: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_coin)],
        RF_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_date)],
        RF_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_hash)],
        RF_PROOF: [
    MessageHandler(
        filters.PHOTO | filters.Document.ALL,
        refund_proof,
    )
],
        RF_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), refund_description)
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
            MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), check_status)
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
                filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ Cancel$"),
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


def get_qwallet(uid):
    f="wallets.csv"
    import csv,os
    if not os.path.exists(f):
        with open(f,"w",newline="",encoding="utf-8") as h:
            csv.writer(h).writerow(["User ID","Quantro"])
    rows=list(csv.reader(open(f,encoding="utf-8")))
    for r in rows[1:]:
        if r and r[0]==str(uid): return float(r[1])
    with open(f,"a",newline="",encoding="utf-8") as h:
        csv.writer(h).writerow([uid,"0.00"])
    return 0.0
def set_qwallet(uid,b):
    import csv,os
    f="wallets.csv"
    if not os.path.exists(f):
        open(f,"w").write("User ID,Quantro\n")
    rows=list(csv.reader(open(f,encoding="utf-8")))
    out=[rows[0]];found=False
    for r in rows[1:]:
        if r and r[0]==str(uid):
            r[1]=f"{b:.2f}";found=True
        out.append(r)
    if not found: out.append([uid,f"{b:.2f}"])
    csv.writer(open(f,"w",newline="",encoding="utf-8")).writerows(out)

def log_wallet_transaction(uid,action,amount,balance):
    import csv,os,datetime
    f="wallet_transactions.csv"
    exists=os.path.exists(f)
    with open(f,"a",newline="",encoding="utf-8") as h:
        w=csv.writer(h)
        if not exists:
            w.writerow(["User ID","Action","Amount","Balance","Timestamp"])
        w.writerow([uid,action,f"{amount:.2f}",f"{balance:.2f}",datetime.datetime.now().isoformat()])


async def wallethistory(update,context):
    if update.effective_user.id!=ADMIN_ID:
        return
    if len(context.args)!=1:
        await update.message.reply_text("Usage: /wallethistory USER_ID");return
    uid=context.args[0]
    import csv,os
    f="wallet_transactions.csv"
    if not os.path.exists(f):
        await update.message.reply_text("No transactions.");return
    lines=[]
    with open(f,encoding="utf-8") as h:
        r=csv.reader(h);next(r,None)
        for row in r:
            if row and row[0]==uid:
                lines.append(f"{row[1]} ${row[2]} -> ${row[3]}\n{row[4]}")
    await update.message.reply_text("\n\n".join(lines) if lines else "No transactions for this user.")

async def addbalance(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid,amt=context.args;bal=get_qwallet(uid)+float(amt);set_qwallet(uid,bal)
    await context.bot.send_message(chat_id=int(uid),text=f"💳 Your Quantro Network Wallet has been credited.\nAmount Added: ${float(amt):.2f}\nNew Balance: ${bal:.2f}")
    await update.message.reply_text(f"✅ Added ${float(amt):.2f} to {uid}. New balance: ${bal:.2f}")
async def subbalance(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid,amt=context.args;bal=max(0,get_qwallet(uid)-float(amt));set_qwallet(uid,bal)
    await context.bot.send_message(chat_id=int(uid),text=f"💳 Your Quantro Network Wallet has been credited.\nAmount Added: ${float(amt):.2f}\nNew Balance: ${bal:.2f}")
    await update.message.reply_text(f"✅ Added ${float(amt):.2f} to {uid}. New balance: ${bal:.2f}")



def get_affiliate_wallet(uid):
    import csv, os
    f="affiliate_wallets.csv"
    if not os.path.exists(f):
        with open(f,"w",newline="",encoding="utf-8") as h:
            csv.writer(h).writerow(["User ID","Affiliate"])
    rows=list(csv.reader(open(f,encoding="utf-8")))
    for r in rows[1:]:
        if r and r[0]==str(uid):
            return float(r[1])
    with open(f,"a",newline="",encoding="utf-8") as h:
        csv.writer(h).writerow([uid,"0.00"])
    return 0.0

def set_affiliate_wallet(uid,balance):
    import csv, os
    f="affiliate_wallets.csv"
    if not os.path.exists(f):
        with open(f,"w",newline="",encoding="utf-8") as h:
            csv.writer(h).writerow(["User ID","Affiliate"])
    rows=list(csv.reader(open(f,encoding="utf-8")))
    out=[rows[0]]
    found=False
    for r in rows[1:]:
        if r and r[0]==str(uid):
            r[1]=f"{balance:.2f}"
            found=True
        out.append(r)
    if not found:
        out.append([uid,f"{balance:.2f}"])
    csv.writer(open(f,"w",newline="",encoding="utf-8")).writerows(out)

def log_affiliate(uid,action,amount,balance):
    import csv,os,datetime
    f="affiliate_transactions.csv"
    exists=os.path.exists(f)
    with open(f,"a",newline="",encoding="utf-8") as h:
        w=csv.writer(h)
        if not exists:
            w.writerow(["User ID","Action","Amount","Balance","Timestamp"])
        w.writerow([uid,action,f"{amount:.2f}",f"{balance:.2f}",datetime.datetime.now().isoformat()])

async def addaffiliate(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid,amt=context.args
    bal=get_affiliate_wallet(uid)+float(amt)
    set_affiliate_wallet(uid,bal)
    log_affiliate(uid,"Credit",float(amt),bal)
    await context.bot.send_message(chat_id=int(uid),text=f"🤝 Affiliate Wallet credited\n+${float(amt):.2f}\nBalance: ${bal:.2f}")
    await update.message.reply_text("Affiliate balance updated.")

async def subaffiliate(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid,amt=context.args
    bal=max(0,get_affiliate_wallet(uid)-float(amt))
    set_affiliate_wallet(uid,bal)
    log_affiliate(uid,"Debit",float(amt),bal)
    await context.bot.send_message(chat_id=int(uid),text=f"🤝 Affiliate Wallet debited\n-${float(amt):.2f}\nBalance: ${bal:.2f}")
    await update.message.reply_text("Affiliate balance updated.")

async def affiliatehistory(update,context):
    if update.effective_user.id!=ADMIN_ID:return
    uid=context.args[0]
    import csv,os
    f="affiliate_transactions.csv"
    if not os.path.exists(f):
        await update.message.reply_text("No records.");return
    lines=[]
    with open(f,encoding="utf-8") as h:
        r=csv.reader(h);next(r,None)
        for row in r:
            if row and row[0]==uid:
                lines.append(f"{row[1]} ${row[2]} -> ${row[3]}\n{row[4]}")
    await update.message.reply_text("\n\n".join(lines) if lines else "No records.")

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

app.add_handler(CommandHandler("update", update_status))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addbalance", addbalance))
app.add_handler(CommandHandler("subbalance", subbalance))
app.add_handler(CommandHandler("wallethistory", wallethistory))
app.add_handler(CommandHandler("addaffiliate", addaffiliate))
app.add_handler(CommandHandler("subaffiliate", subaffiliate))
app.add_handler(CommandHandler("affiliatehistory", affiliatehistory))

app.add_handler(MessageHandler(filters.Regex("^🏠 Main Menu$"), main_menu))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buttons))

# ==========================
# RENDER WEB SERVER
# ==========================

web = Flask(__name__)

@web.route("/")
def home():
    return "Quantro Network Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

print("✅ Starting web server...")

threading.Thread(target=run_web).start()

print("✅ Bot is running...")

app.run_polling()
# Wallet system TODO implemented externally.
