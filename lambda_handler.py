import json
import os
import urllib.request


def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
                                 "Content-Type": "application/json"})
    urllib.request.urlopen(req)


def handler(event, context):
    try:
        token = os.environ["TELEGRAM_TOKEN"]
        body = json.loads(event.get("body", "{}"))

        message = body.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not chat_id:
            return {"statusCode": 200, "body": "OK"}

        if text == "/start":
            send_message(token, chat_id,
                         "Hi! I am your Study Assistant bot.\n\nSend me a PDF, PowerPoint or Word file and I will generate 10 quiz questions from it!")
        else:
            send_message(token, chat_id,
                         "Please send me a file to start a quiz!")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

    return {"statusCode": 200, "body": "OK"}
