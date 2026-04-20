import json
import os
import urllib.request
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('study-assistant-sessions')
sqs = boto3.client('sqs', region_name='us-east-1')
QUEUE_URL = os.environ.get('SQS_QUEUE_URL')


def send_message(token, chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data = json.dumps(payload).encode("utf-8")
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
                         "Hi! I am your Study Assistant bot.\n\nSend me a PDF, PowerPoint or Word file and I will generate 10 quiz questions from it!\n\nCommands:\n/difficulty - choose difficulty level\n/language - choose language\n/flashcard - flashcard mode")

        elif text == "/difficulty":
            keyboard = {
                "keyboard": [
                    [{"text": "Easy"}, {"text": "Medium"}, {"text": "Hard"}]
                ],
                "one_time_keyboard": True,
                "resize_keyboard": True
            }
            send_message(token, chat_id, "Choose your difficulty level:",
                         reply_markup=json.dumps(keyboard))

        elif text == "/language":
            keyboard = {
                "keyboard": [
                    [{"text": "English"}, {"text": "Amharic"}, {"text": "French"}]
                ],
                "one_time_keyboard": True,
                "resize_keyboard": True
            }
            send_message(token, chat_id, "Choose your language:",
                         reply_markup=json.dumps(keyboard))

        elif text == "/flashcard":
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET mode = :m',
                ExpressionAttributeValues={':m': 'flashcard'}
            )
            send_message(
                token, chat_id, "Flashcard mode on! Send me a file and I will show you key concepts.")

        elif text in ["Easy", "Medium", "Hard"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET difficulty = :d',
                ExpressionAttributeValues={':d': text}
            )
            send_message(
                token, chat_id, f"Difficulty set to {text}! Now send me a file to start.")

        elif text in ["English", "Amharic", "French"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET language = :l',
                ExpressionAttributeValues={':l': text}
            )
            send_message(
                token, chat_id, f"Language set to {text}! Now send me a file to start.")

        elif text == "Yes!":
            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item', {})
            waiting_for = session.get('waiting_for', '')
            file_id = session.get('saved_file_id', '')
            file_name = session.get('saved_file_name', '')
            language = session.get('language', 'English')

            if waiting_for == 'medium_confirm':
                send_message(
                    token, chat_id, "Great! Generating Medium questions from the same file...")
                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps({
                        "chat_id": chat_id,
                        "file_id": file_id,
                        "file_name": file_name,
                        "difficulty": "Medium",
                        "language": language,
                        "mode": "quiz",
                        "total_score": int(session.get('total_score', 0))
                    })
                )
            elif waiting_for == 'hard_confirm':
                send_message(
                    token, chat_id, "Let's go! Generating Hard questions from the same file...")
                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps({
                        "chat_id": chat_id,
                        "file_id": file_id,
                        "file_name": file_name,
                        "difficulty": "Hard",
                        "language": language,
                        "mode": "quiz",
                        "total_score": int(session.get('total_score', 0))
                    })
                )

        elif text == "No thanks":
            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item', {})
            total_score = int(session.get('total_score', 0))
            send_message(token, chat_id,
                         f"No problem! Your total score so far: {total_score} points.\n\nSend me another file to start a new quiz!")

        elif document:
            file_name = document.get("file_name", "file")
            file_id = document.get("file_id")

            response = table.get_item(Key={'chat_id': chat_id})
            settings = response.get('Item', {})
            difficulty = settings.get('difficulty', 'Easy')
            language = settings.get('language', 'English')
            mode = settings.get('mode', 'quiz')

            send_message(token, chat_id,
                         f"Got your file!\nDifficulty: {difficulty}\nLanguage: {language}\nMode: {mode}\n\nProcessing... I will send you questions shortly!")

            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps({
                    "chat_id": chat_id,
                    "file_id": file_id,
                    "file_name": file_name,
                    "difficulty": difficulty,
                    "language": language,
                    "mode": mode,
                    "total_score": 0
                })
            )

        elif text.upper() in ["A", "B", "C", "D"]:
            answer = text.upper()

            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item')

            if not session or 'questions' not in session:
                send_message(token, chat_id,
                             "Please send me a file first to start a quiz!")
                return {"statusCode": 200, "body": "OK"}

            questions = json.loads(session['questions'])
            current = int(session.get('question_current', 0))
            score = int(session.get('score', 0))
            question = questions[current]
            correct = question["answer"]

            if answer == correct:
                score += 1
                send_message(token, chat_id,
                             f"Correct! Well done! 🎉\n\nScore so far: {score} out of {current + 1}")
            else:
                send_message(token, chat_id,
                             f"Wrong! The correct answer is {correct}.\n\nExplanation: {question['explanation']}\n\nScore so far: {score} out of {current + 1}")

            current += 1

            if current >= len(questions):
                difficulty = session.get('difficulty', 'Easy')
                total_score = int(session.get('total_score', 0)) + score

                if difficulty == 'Easy':
                    keyboard = {
                        "keyboard": [[{"text": "Yes!"}, {"text": "No thanks"}]],
                        "one_time_keyboard": True,
                        "resize_keyboard": True
                    }
                    send_message(token, chat_id,
                                 f"Easy quiz complete! Your score is {score} out of {len(questions)}.\n\nReady to try Medium difficulty with the same file?",
                                 reply_markup=json.dumps(keyboard))
                    table.update_item(
                        Key={'chat_id': chat_id},
                        UpdateExpression='SET waiting_for = :w, total_score = :t, saved_file_id = :f, saved_file_name = :n',
                        ExpressionAttributeValues={
                            ':w': 'medium_confirm',
                            ':t': total_score,
                            ':f': session.get('file_id', ''),
                            ':n': session.get('file_name', '')
                        }
                    )
                elif difficulty == 'Medium':
                    keyboard = {
                        "keyboard": [[{"text": "Yes!"}, {"text": "No thanks"}]],
                        "one_time_keyboard": True,
                        "resize_keyboard": True
                    }
                    send_message(token, chat_id,
                                 f"Medium quiz complete! Your score is {score} out of {len(questions)}.\n\nReady for the Hard difficulty challenge?",
                                 reply_markup=json.dumps(keyboard))
                    table.update_item(
                        Key={'chat_id': chat_id},
                        UpdateExpression='SET waiting_for = :w, total_score = :t',
                        ExpressionAttributeValues={
                            ':w': 'hard_confirm',
                            ':t': total_score
                        }
                    )
                elif difficulty == 'Hard':
                    send_message(token, chat_id,
                                 f"Hard quiz complete! Your score is {score} out of {len(questions)}.\n\nTotal score across all difficulties: {total_score} out of 30!\n\nAmazing work! Send me another file to start again.")
                    table.update_item(
                        Key={'chat_id': chat_id},
                        UpdateExpression='REMOVE questions, question_current, score, difficulty, total_score, waiting_for, saved_file_id, saved_file_name, mode',
                        ExpressionAttributeNames={}
                    )
            else:
                table.update_item(
                    Key={'chat_id': chat_id},
                    UpdateExpression='SET question_current = :c, score = :s',
                    ExpressionAttributeValues={':c': current, ':s': score}
                )
                next_question = questions[current]
                text = f"Question {current + 1} of {len(questions)} ({session.get('difficulty', 'Easy')}):\n\n"
                text += f"{next_question['question']}\n\n"
                for option in next_question["options"]:
                    text += f"{option}\n"
                text += "\nReply with A, B, C or D"
                send_message(token, chat_id, text)

        else:
            send_message(
                token, chat_id, "Please send me a file to start a quiz!\n\nOr use:\n/difficulty - set difficulty\n/language - set language\n/flashcard - flashcard mode")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

    return {"statusCode": 200, "body": "OK"}
