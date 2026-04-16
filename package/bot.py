import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from extractor import extract_text
from quiz import generate_questions

logging.basicConfig(level=logging.INFO)

user_sessions = {}


def get_token():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("TELEGRAM_TOKEN")
    return token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I am your Study Assistant bot.\n\nSend me a PDF, PowerPoint or Word file and I will generate 10 quiz questions from it!"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text("Got your file! Extracting text and generating questions, please wait...")

    file = await update.message.document.get_file()
    file_name = update.message.document.file_name
    file_path = f"/tmp/{file_name}"
    await file.download_to_drive(file_path)

    text = extract_text(file_path)

    if not text.strip():
        await update.message.reply_text("Sorry I could not extract any text from that file. Please try another one.")
        return

    await update.message.reply_text("Generating your 10 questions... this may take a few seconds!")

    questions = generate_questions(text)

    if not questions:
        await update.message.reply_text("Sorry I could not generate questions from that file. Please try another one.")
        return

    user_sessions[user_id] = {
        "questions": questions,
        "current": 0,
        "score": 0
    }

    await send_question(update, user_id)


async def send_question(update: Update, user_id: int):
    session = user_sessions[user_id]
    current = session["current"]
    question = session["questions"][current]

    text = f"Question {current + 1} of {len(session['questions'])}:\n\n"
    text += f"{question['question']}\n\n"
    for option in question["options"]:
        text += f"{option}\n"
    text += "\nReply with A, B, C or D"

    await update.message.reply_text(text)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    answer = update.message.text.strip().upper()

    if user_id not in user_sessions:
        await update.message.reply_text("Please send me a file first to start a quiz!")
        return

    if answer not in ["A", "B", "C", "D"]:
        await update.message.reply_text("Please reply with A, B, C or D")
        return

    session = user_sessions[user_id]
    current = session["current"]
    question = session["questions"][current]
    correct = question["answer"]

    if answer == correct:
        session["score"] += 1
        await update.message.reply_text("Correct! Well done!")
    else:
        await update.message.reply_text(
            f"Wrong! The correct answer is {correct}.\n\n"
            f"Explanation: {question['explanation']}"
        )

    session["current"] += 1

    if session["current"] >= len(session["questions"]):
        score = session["score"]
        total = len(session["questions"])
        await update.message.reply_text(
            f"Quiz complete! Your score is {score} out of {total}.\n\n"
            f"Send me another file to start a new quiz!"
        )
        del user_sessions[user_id]
    else:
        await send_question(update, user_id)

if __name__ == "__main__":
    TOKEN = get_token()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_answer))
    print("Bot is running...")
    app.run_polling()
