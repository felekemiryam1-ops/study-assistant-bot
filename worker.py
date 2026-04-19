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
    token = os.environ["TELEGRAM_TOKEN"]

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            chat_id = body["chat_id"]
            file_id = body["file_id"]
            file_name = body["file_name"]

            send_message(token, chat_id, "Downloading your file...")

            file_url = get_file_url(token, file_id)
            local_path = f"/tmp/{file_name}"
            download_file(file_url, local_path)

            from extractor import extract_text
            text_content = extract_text(local_path)

            if not text_content.strip():
                send_message(
                    token, chat_id, "Sorry I could not extract any text from that file. Please try another one.")
                continue

            send_message(
                token, chat_id, "Generating your 10 questions... this may take a moment!")

            from quiz import generate_questions
            questions = generate_questions(text_content)

            if not questions:
                send_message(
                    token, chat_id, "Sorry I could not generate questions. Please try another file.")
                continue

            user_sessions[chat_id] = {
                "questions": questions,
                "current": 0,
                "score": 0
            }

            question = questions[0]
            text = f"Question 1 of {len(questions)}:\n\n"
            text += f"{question['question']}\n\n"
            for option in question["options"]:
                text += f"{option}\n"
            text += "\nReply with A, B, C or D"
            send_message(token, chat_id, text)

        except Exception as e:
            print(f"Error processing record: {str(e)}")
            import traceback
            traceback.print_exc()

    return {"statusCode": 200}
