import json
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters


async def main(token, body):
    from bot import start, handle_document, handle_answer
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_answer))
    await app.initialize()
    update = Update.de_json(body, app.bot)
    await app.process_update(update)
    await app.shutdown()


def handler(event, context):
    try:
        token = os.environ['TELEGRAM_TOKEN']
        body = json.loads(event.get('body', '{}'))
        asyncio.run(main(token, body))
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
