import json
import os
import urllib.request
import urllib.parse


def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
                                 "Content-Type": "application/json"})
    urllib.request.urlopen(req)


def get_file_url(token, file_id):
    url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    file_path = data["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{token}/{file_path}"


def download_file(file_url, local_path):
    urllib.request.urlretrieve(file_url, local_path)


user_sessions = {}


def handler(event, context):
    try:
        token = os.environ["TELEGRAM_TOKEN"]
        body = json.loads(event.get("body", "{}"))

        message = body.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        document = message.get("document")

        if not chat_id:
            return {"statusCode": 200, "body": "OK"}

        if text == "/start":
            send_message(token, chat_id,
                         "Hi! I am your Study Assistant bot.\n\nSend me a PDF, PowerPoint or Word file and I will generate 10 quiz questions from it!")

        elif document:
            file_name = document.get("file_name", "file")
            file_id = document.get("file_id")

            send_message(
                token, chat_id, "Got your file! Extracting text and generating questions, please wait...")

            file_url = get_file_url(token, file_id)
            local_path = f"/tmp/{file_name}"
            download_file(file_url, local_path)

            from extractor import extract_text
            text_content = extract_text(local_path)

            if not text_content.strip():
                send_message(
                    token, chat_id, "Sorry I could not extract any text from that file. Please try another one.")
                return {"statusCode": 200, "body": "OK"}

            send_message(
                token, chat_id, "Generating your 10 questions... this may take a few seconds!")

            from quiz import generate_questions
            questions = generate_questions(text_content)

            if not questions:
                send_message(
                    token, chat_id, "Sorry I could not generate questions. Please try another file.")
                return {"statusCode": 200, "body": "OK"}

            user_sessions[chat_id] = {
                "questions": questions,
                "current": 0,
                "score": 0
            }

            send_first_question(token, chat_id)

        elif text.upper() in ["A", "B", "C", "D"]:
            handle_answer(token, chat_id, text.upper())

        else:
            send_message(token, chat_id,
                         "Please send me a file to start a quiz!")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

    return {"statusCode": 200, "body": "OK"}


def send_first_question(token, chat_id):
    session = user_sessions[chat_id]
    question = session["questions"][0]
    text = f"Question 1 of {len(session['questions'])}:\n\n"
    text += f"{question['question']}\n\n"
    for option in question["options"]:
        text += f"{option}\n"
    text += "\nReply with A, B, C or D"
    send_message(token, chat_id, text)


def handle_answer(token, chat_id, answer):
    if chat_id not in user_sessions:
        send_message(token, chat_id,
                     "Please send me a file first to start a quiz!")
        return

    session = user_sessions[chat_id]
    current = session["current"]
    question = session["questions"][current]
    correct = question["answer"]

    if answer == correct:
        session["score"] += 1
        send_message(token, chat_id, "Correct! Well done!")
    else:
        send_message(token, chat_id,
                     f"Wrong! The correct answer is {correct}.\n\nExplanation: {question['explanation']}")

    session["current"] += 1

    if session["current"] >= len(session["questions"]):
        score = session["score"]
        total = len(session["questions"])
        send_message(token, chat_id,
                     f"Quiz complete! Your score is {score} out of {total}.\n\nSend me another file to start a new quiz!")
        del user_sessions[chat_id]
    else:
        session = user_sessions[chat_id]
        current = session["current"]
        question = session["questions"][current]
        text = f"Question {current + 1} of {len(session['questions'])}:\n\n"
        text += f"{question['question']}\n\n"
        for option in question["options"]:
            text += f"{option}\n"
        text += "\nReply with A, B, C or D"
        send_message(token, chat_id, text)
