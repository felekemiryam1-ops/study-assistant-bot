import json
import os
import urllib.request
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('study-assistant-sessions')


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
    print(f"Getting file URL for file_id: {file_id}")
    url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    file_path = data["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{token}/{file_path}"


def download_file(file_url, local_path):
    print(f"Downloading file to: {local_path}")
    urllib.request.urlretrieve(file_url, local_path)
    print("Download complete")


def handler(event, context):
    print("Worker started")
    token = os.environ["TELEGRAM_TOKEN"]

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            chat_id = body["chat_id"]
            file_id = body["file_id"]
            file_name = body["file_name"]

            print(f"Processing file for chat_id: {chat_id}")

            send_message(token, chat_id, "Downloading your file...")
            file_url = get_file_url(token, file_id)
            local_path = f"/tmp/{file_name}"
            download_file(file_url, local_path)

            send_message(token, chat_id, "Extracting text from your file...")
            from extractor import extract_text
            text_content = extract_text(local_path)
            print(f"Extracted {len(text_content)} characters")

            if not text_content.strip():
                send_message(
                    token, chat_id, "Sorry I could not extract any text. Please try another file.")
                continue

            send_message(
                token, chat_id, "Generating your 10 questions... this may take a moment!")
            from quiz import generate_questions
            questions = generate_questions(text_content)
            print(f"Generated {len(questions)} questions")

            if not questions:
                send_message(
                    token, chat_id, "Sorry I could not generate questions. Please try another file.")
                continue

            table.put_item(Item={
                'chat_id': chat_id,
                'questions': json.dumps(questions),
                'question_current': 0,
                'score': 0
            })
            print("Session saved to DynamoDB")

            question = questions[0]
            text = f"Question 1 of {len(questions)}:\n\n"
            text += f"{question['question']}\n\n"
            for option in question["options"]:
                text += f"{option}\n"
            text += "\nReply with A, B, C or D"
            send_message(token, chat_id, text)
            print("First question sent!")

        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    return {"statusCode": 200}
