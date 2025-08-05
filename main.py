from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import sqlite3
from db import create_users_table

ASK_NAME = 1  # Conversation bosqichi
DELETE_CHOICE = 2  # Conversation bosqichi (o'chirish)
EDIT_CHOICE = 3
ASK_NEW_NAME = 4


# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alaykum! Ismingizni kiriting:")
    return ASK_NAME

# Ismni qabul qilish va bazaga yozish
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    telegram_id = update.message.from_user.id

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (telegram_id, name) VALUES (?, ?)", (telegram_id, name))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Rahmat, {name}! Ismingiz saqlandi.")
    return ConversationHandler.END

# Users ko'rish
async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT name FROM users")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Hech qanday foydalanuvchi topilmadi.")
        return

    user_list = "\n".join([f"{i+1}. {row[0]}" for i, row in enumerate(rows)])
    await update.message.reply_text(f"Foydalanuvchilar ro'yxati:\n{user_list}")

# Users o'chirish
async def delete_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM users")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("O‘chirish uchun foydalanuvchi yo‘q.")
        return ConversationHandler.END

    context.user_data["user_list"] = rows  # vaqtincha saqlab turamiz
    msg = "O‘chirmoqchi bo‘lgan foydalanuvchini tanlang:\n"
    msg += "\n".join([f"{i+1}. {row[1]}" for i, row in enumerate(rows)])
    msg += "\n\nIltimos, foydalanuvchi raqamini yozing:"
    await update.message.reply_text(msg)
    return DELETE_CHOICE

async def delete_user_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        choice = int(update.message.text)
        user_list = context.user_data["user_list"]
        selected_user = user_list[choice - 1]
        user_id = selected_user[0]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"{selected_user[1]} muvaffaqiyatli o‘chirildi.")
    except:
        await update.message.reply_text("Noto‘g‘ri raqam. Amaliyot bekor qilindi.")
    return ConversationHandler.END


#Users o'zgartirish
async def edit_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM users")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("O‘zgartirish uchun foydalanuvchi yo‘q.")
        return ConversationHandler.END

    context.user_data["user_list"] = rows
    msg = "Qaysi foydalanuvchining ismini o‘zgartirmoqchisiz?\n"
    msg += "\n".join([f"{i+1}. {row[1]}" for i, row in enumerate(rows)])
    msg += "\n\nIltimos, foydalanuvchi raqamini yozing:"
    await update.message.reply_text(msg)
    return EDIT_CHOICE

async def ask_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        choice = int(update.message.text)
        user_list = context.user_data["user_list"]
        selected_user = user_list[choice - 1]
        context.user_data["edit_user_id"] = selected_user[0]
        context.user_data["edit_old_name"] = selected_user[1]

        await update.message.reply_text(
            f"{selected_user[1]} uchun yangi ismini kiriting:"
        )
        return ASK_NEW_NAME
    except:
        await update.message.reply_text("Noto‘g‘ri raqam. Bekor qilindi.")
        return ConversationHandler.END
    
#Yangi ismni saqlash
async def save_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    user_id = context.user_data["edit_user_id"]
    old_name = context.user_data["edit_old_name"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET name = ? WHERE id = ?", (new_name, user_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"{old_name} ismi {new_name} ga o‘zgartirildi.")
    return ConversationHandler.END


# Bekor qilish (ixtiyoriy)
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END

# Main
if __name__ == '__main__':
    create_users_table()

    app = ApplicationBuilder().token("8308883171:AAF5-XE-lYHT17IOFRH0rADSc6afsjNR_78").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("users", show_users))
    
    delete_handler = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_user_start)],
        states={
            DELETE_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_user_finish)],
        },
        fallbacks=[]
    )
    app.add_handler(delete_handler)

    edit_handler = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_user_start)],
        states={
            EDIT_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_new_name)],
            ASK_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_name)],
        },
        fallbacks=[]
    )

    app.add_handler(edit_handler)

    app.run_polling()
