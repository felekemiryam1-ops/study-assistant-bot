import json
import os
import urllib.request
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('study-assistant-sessions')
sqs = boto3.client('sqs', region_name='us-east-1')
QUEUE_URL = os.environ.get('SQS_QUEUE_URL')


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
                token, chat_id, "Got your file! I am processing it and will send you questions shortly...")

            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps({
                    "chat_id": chat_id,
                    "file_id": file_id,
                    "file_name": file_name
                })
            )

        elif text.upper() in ["A", "B", "C", "D"]:
            answer = text.upper()

            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item')

            if not session:
                send_message(token, chat_id,
                             "Please send me a file first to start a quiz!")
                return {"statusCode": 200, "body": "OK"}

            questions = json.loads(session['questions'])
            current = int(session['current'])
            score = int(session['score'])
            question = questions[current]
            correct = question["answer"]

            if answer == correct:
                score += 1
                send_message(token, chat_id, "Correct! Well done!")
            else:
                send_message(token, chat_id,
                             f"Wrong! The correct answer is {correct}.\n\nExplanation: {question['explanation']}")

            current += 1

            if current >= len(questions):
                send_message(token, chat_id,
                             f"Quiz complete! Your score is {score} out of {len(questions)}.\n\nSend me another file to start a new quiz!")
                table.delete_item(Key={'chat_id': chat_id})
            else:
                table.update_item(
                    Key={'chat_id': chat_id},
                    UpdateExpression='SET current = :c, score = :s',
                    ExpressionAttributeValues={':c': current, ':s': score}
                )
                next_question = questions[current]
                text = f"Question {current + 1} of {len(questions)}:\n\n"
                text += f"{next_question['question']}\n\n"
                for option in next_question["options"]:
                    text += f"{option}\n"
                text += "\nReply with A, B, C or D"
                send_message(token, chat_id, text)

        else:
            send_message(token, chat_id,
                         "Please send me a file to start a quiz!")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

    return {"statusCode": 200, "body": "OK"}
