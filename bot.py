from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from storage import init_db, save_user, load_user, save_purchase  

SALARY, HOURS_MODE, CALCULATE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_user(user_id)

    if data:
        salary, hours = data
        hourly_rate = salary / hours
        context.user_data["salary"] = salary
        context.user_data["hourly_rate"] = hourly_rate
        await update.message.reply_text(
            f"Я тебя помню! 🧠\n"
            f"Зарплата: {salary} руб, часов в месяц: {hours}\n"
            f"Стоимость часа: {hourly_rate:.2f} руб\n\n"
            "Можешь прислать цену покупки, и я скажу, сколько нужно отработать.\n"
            "Или напиши /reset, чтобы ввести заново."
        )
        return CALCULATE
    else:
        await update.message.reply_text("Привет! Сколько ты зарабатываешь в месяц (в рублях)?")
        return SALARY

async def salary_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        salary = float(update.message.text)
        context.user_data["salary"] = salary
        await update.message.reply_text(
            "Сколько часов в день ты работаешь?\n"
            "Напиши `8` для стандартного графика или укажи своё количество."
        )
        return HOURS_MODE
    except ValueError:
        await update.message.reply_text("Пожалуйста, введи число. Попробуем ещё раз:")
        return SALARY

async def hours_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours_per_day = float(update.message.text)
        days_per_month = 22  # среднее количество рабочих дней
        total_hours = hours_per_day * days_per_month
        salary = context.user_data["salary"]
        hourly_rate = salary / total_hours
        context.user_data["hourly_rate"] = hourly_rate

        user_id = update.effective_user.id
        save_user(user_id, salary, total_hours)

        await update.message.reply_text(
            f"Твоя стоимость часа: {hourly_rate:.2f} руб.\n"
            "Теперь можешь прислать мне цену покупки, а я скажу, сколько нужно на неё отработать.\n"
            "Или напиши /reset, чтобы начать заново."
        )
        return CALCULATE
    except ValueError:
        await update.message.reply_text("Пожалуйста, введи число.")
        return HOURS_MODE

async def calculate_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        hourly_rate = context.user_data.get("hourly_rate")

        if hourly_rate is None:
            await update.message.reply_text("Сначала нужно ввести зарплату. Напиши /start.")
            return SALARY

        hours_needed = amount / hourly_rate

        # Сохраняем покупку в БД
        user_id = update.effective_user.id
        save_purchase(user_id, amount, hours_needed)

        await update.message.reply_text(
            f"Чтобы купить это, тебе нужно отработать {hours_needed:.2f} часов."
        )
    except ValueError:
        await update.message.reply_text("Пожалуйста, введи число.")
    return CALCULATE

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Давай начнём сначала. Сколько ты зарабатываешь в месяц?")
    return SALARY

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("До встречи!")
    return ConversationHandler.END

if __name__ == "__main__":
    import os

    init_db()
    TOKEN = os.getenv("TG_BOT_TOKEN")  
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_input)],
            HOURS_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hours_input)],
            CALCULATE: [
                CommandHandler("reset", reset),
                MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_purchase),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Бот запущен...")
    app.run_polling()
