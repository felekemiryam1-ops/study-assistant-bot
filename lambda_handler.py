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
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)


def main_menu():
    return json.dumps({
        "keyboard": [
            [{"text": "📚 Start Quiz"}, {"text": "🃏 Flashcard Mode"}],
            [{"text": "⚙️ Settings"}, {"text": "❓ Help"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    })


def settings_menu():
    return json.dumps({
        "keyboard": [
            [{"text": "🎯 Difficulty"}, {"text": "🌍 Language"}],
            [{"text": "📊 My Settings"}, {"text": "🏠 Main Menu"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    })


def difficulty_menu():
    return json.dumps({
        "keyboard": [
            [{"text": "🟢 Easy"}, {"text": "🟡 Medium"}, {"text": "🔴 Hard"}],
            [{"text": "🔙 Back to Settings"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    })


def language_menu():
    return json.dumps({
        "keyboard": [
            [{"text": "🇬🇧 English"}, {"text": "🇪🇹 Amharic"}, {"text": "🇫🇷 French"}],
            [{"text": "🔙 Back to Settings"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    })


def quiz_menu():
    return json.dumps({
        "keyboard": [
            [{"text": "A"}, {"text": "B"}, {"text": "C"}, {"text": "D"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    })


def flashcard_menu():
    return json.dumps({
        "keyboard": [
            [{"text": "👆 Flip Card"}],
            [{"text": "⏭️ Skip"}, {"text": "🏠 Main Menu"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    })


def flashcard_next_menu():
    return json.dumps({
        "keyboard": [
            [{"text": "➡️ Next Card"}],
            [{"text": "🏠 Main Menu"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    })


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
                "Hi! I am your Study Assistant Bot! 👋\n\nI will quiz you on any study material you send me.\n\nUse the menu below to get started!",
                reply_markup=main_menu())

        elif text in ["📚 Start Quiz", "/quiz"]:
            response = table.get_item(Key={'chat_id': chat_id})
            settings = response.get('Item', {})
            difficulty = settings.get('quiz_difficulty', 'Easy')
            quiz_language = settings.get('quiz_language', 'English')
            send_message(token, chat_id,
                f"📚 Quiz Mode\n\nCurrent settings:\n🎯 Difficulty: {difficulty}\n🌍 Language: {quiz_language}\n\nNow send me your file — PDF, PowerPoint or Word!",
                reply_markup=main_menu())

        elif text in ["🃏 Flashcard Mode", "/flashcard"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET quiz_mode = :m',
                ExpressionAttributeValues={':m': 'flashcard'}
            )
            send_message(token, chat_id,
                "🃏 Flashcard Mode activated!\n\nSend me your file and I will create flashcards from it!\n\nYou will see the concept first, then tap to flip and see the explanation!",
                reply_markup=main_menu())

        elif text in ["⚙️ Settings", "/settings"]:
            response = table.get_item(Key={'chat_id': chat_id})
            settings = response.get('Item', {})
            difficulty = settings.get('quiz_difficulty', 'Easy')
            quiz_language = settings.get('quiz_language', 'English')
            mode = settings.get('quiz_mode', 'quiz')
            send_message(token, chat_id,
                f"⚙️ Settings\n\nCurrent settings:\n🎯 Difficulty: {difficulty}\n🌍 Language: {quiz_language}\n📖 Mode: {mode}\n\nWhat would you like to change?",
                reply_markup=settings_menu())

        elif text in ["🎯 Difficulty", "/difficulty"]:
            send_message(token, chat_id,
                "🎯 Choose your difficulty level:",
                reply_markup=difficulty_menu())

        elif text in ["🌍 Language", "/language"]:
            send_message(token, chat_id,
                "🌍 Choose your language:",
                reply_markup=language_menu())

        elif text == "📊 My Settings":
            response = table.get_item(Key={'chat_id': chat_id})
            settings = response.get('Item', {})
            difficulty = settings.get('quiz_difficulty', 'Easy')
            quiz_language = settings.get('quiz_language', 'English')
            mode = settings.get('quiz_mode', 'quiz')
            send_message(token, chat_id,
                f"📊 Your current settings:\n\n🎯 Difficulty: {difficulty}\n🌍 Language: {quiz_language}\n📖 Mode: {mode}",
                reply_markup=settings_menu())

        elif text == "🏠 Main Menu":
            send_message(token, chat_id,
                "🏠 Main Menu",
                reply_markup=main_menu())

        elif text == "🔙 Back to Settings":
            send_message(token, chat_id,
                "⚙️ Settings",
                reply_markup=settings_menu())

        elif text in ["❓ Help", "/help"]:
            send_message(token, chat_id,
                "❓ Help\n\n📚 Start Quiz — upload a file and get quizzed\n🃏 Flashcard Mode — flip cards to learn concepts\n⚙️ Settings — change difficulty and language\n\n📁 Supported files:\n• PDF\n• PowerPoint (.pptx)\n• Word (.docx)\n\n🎯 Difficulty levels:\n• Easy — basic facts\n• Medium — understanding\n• Hard — tricky questions\n\n🌍 Languages:\n• English\n• Amharic (አማርኛ)\n• French\n\n💡 Tip: Set difficulty and language BEFORE sending your file!",
                reply_markup=main_menu())

        elif text in ["🟢 Easy", "Easy"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET quiz_difficulty = :d',
                ExpressionAttributeValues={':d': 'Easy'}
            )
            send_message(token, chat_id, "✅ Difficulty set to Easy!", reply_markup=settings_menu())

        elif text in ["🟡 Medium", "Medium"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET quiz_difficulty = :d',
                ExpressionAttributeValues={':d': 'Medium'}
            )
            send_message(token, chat_id, "✅ Difficulty set to Medium!", reply_markup=settings_menu())

        elif text in ["🔴 Hard", "Hard"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET quiz_difficulty = :d',
                ExpressionAttributeValues={':d': 'Hard'}
            )
            send_message(token, chat_id, "✅ Difficulty set to Hard!", reply_markup=settings_menu())

        elif text in ["🇬🇧 English", "English"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET quiz_language = :l',
                ExpressionAttributeValues={':l': 'English'}
            )
            send_message(token, chat_id, "✅ Language set to English!", reply_markup=settings_menu())

        elif text in ["🇪🇹 Amharic", "Amharic"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET quiz_language = :l',
                ExpressionAttributeValues={':l': 'Amharic'}
            )
            send_message(token, chat_id, "✅ Language set to Amharic! (አማርኛ)", reply_markup=settings_menu())

        elif text in ["🇫🇷 French", "French"]:
            table.update_item(
                Key={'chat_id': chat_id},
                UpdateExpression='SET quiz_language = :l',
                ExpressionAttributeValues={':l': 'French'}
            )
            send_message(token, chat_id, "✅ Language set to French!", reply_markup=settings_menu())

        elif text == "👆 Flip Card":
            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item')

            if not session or 'flashcards' not in session:
                send_message(token, chat_id, "Please send me a file first!", reply_markup=main_menu())
                return {"statusCode": 200, "body": "OK"}

            flashcards = json.loads(session['flashcards'])
            current = int(session.get('flashcard_current', 0))
            card = flashcards[current]

            send_message(token, chat_id,
                f"🃏 Flashcard {current + 1} of {len(flashcards)}\n\n❓ {card['concept']}\n\n✅ Answer:\n{card['explanation']}",
                reply_markup=flashcard_next_menu())

        elif text == "➡️ Next Card":
            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item')

            if not session or 'flashcards' not in session:
                send_message(token, chat_id, "Please send me a file first!", reply_markup=main_menu())
                return {"statusCode": 200, "body": "OK"}

            flashcards = json.loads(session['flashcards'])
            current = int(session.get('flashcard_current', 0)) + 1

            if current >= len(flashcards):
                send_message(token, chat_id,
                    f"🎊 You completed all {len(flashcards)} flashcards!\n\nWant to take a quiz on the same material? Send the file again and choose Quiz mode!",
                    reply_markup=main_menu())
                table.delete_item(Key={'chat_id': chat_id})
            else:
                table.update_item(
                    Key={'chat_id': chat_id},
                    UpdateExpression='SET flashcard_current = :c',
                    ExpressionAttributeValues={':c': current}
                )
                card = flashcards[current]
                send_message(token, chat_id,
                    f"🃏 Flashcard {current + 1} of {len(flashcards)}\n\n❓ {card['concept']}\n\nTap to flip and see the answer!",
                    reply_markup=flashcard_menu())

        elif text == "⏭️ Skip":
            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item')

            if not session or 'flashcards' not in session:
                send_message(token, chat_id, "Please send me a file first!", reply_markup=main_menu())
                return {"statusCode": 200, "body": "OK"}

            flashcards = json.loads(session['flashcards'])
            current = int(session.get('flashcard_current', 0)) + 1

            if current >= len(flashcards):
                send_message(token, chat_id,
                    f"🎊 You completed all {len(flashcards)} flashcards!",
                    reply_markup=main_menu())
                table.delete_item(Key={'chat_id': chat_id})
            else:
                table.update_item(
                    Key={'chat_id': chat_id},
                    UpdateExpression='SET flashcard_current = :c',
                    ExpressionAttributeValues={':c': current}
                )
                card = flashcards[current]
                send_message(token, chat_id,
                    f"🃏 Flashcard {current + 1} of {len(flashcards)}\n\n❓ {card['concept']}\n\nTap to flip and see the answer!",
                    reply_markup=flashcard_menu())

        elif text == "Yes!":
            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item', {})
            waiting_for = session.get('waiting_for', '')
            file_id = session.get('saved_file_id', '')
            file_name = session.get('saved_file_name', '')
            quiz_language = session.get('quiz_language', 'English')
            previous_questions = session.get('previous_questions', '[]')

            if waiting_for == 'medium_confirm':
                send_message(token, chat_id, "Great! Generating Medium questions from the same file...")
                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps({
                        "chat_id": chat_id,
                        "file_id": file_id,
                        "file_name": file_name,
                        "difficulty": "Medium",
                        "language": quiz_language,
                        "mode": "quiz",
                        "total_score": int(session.get('total_score', 0)),
                        "previous_questions": previous_questions
                    })
                )
            elif waiting_for == 'hard_confirm':
                send_message(token, chat_id, "Let's go! Generating Hard questions from the same file...")
                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps({
                        "chat_id": chat_id,
                        "file_id": file_id,
                        "file_name": file_name,
                        "difficulty": "Hard",
                        "language": quiz_language,
                        "mode": "quiz",
                        "total_score": int(session.get('total_score', 0)),
                        "previous_questions": previous_questions
                    })
                )

        elif text == "No thanks":
            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item', {})
            total_score = int(session.get('total_score', 0))
            send_message(token, chat_id,
                f"No problem! Your total score so far: {total_score} points.\n\nSend me another file to start a new quiz!",
                reply_markup=main_menu())

        elif document:
            file_name = document.get("file_name", "file")
            file_id = document.get("file_id")

            response = table.get_item(Key={'chat_id': chat_id})
            settings = response.get('Item', {})
            difficulty = settings.get('quiz_difficulty', 'Easy')
            quiz_language = settings.get('quiz_language', 'English')
            mode = settings.get('quiz_mode', 'quiz')

            send_message(token, chat_id,
                f"Got your file! 📁\n\n🎯 Difficulty: {difficulty}\n🌍 Language: {quiz_language}\n📖 Mode: {mode}\n\nProcessing... I will send you questions shortly! ⏳")

            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps({
                    "chat_id": chat_id,
                    "file_id": file_id,
                    "file_name": file_name,
                    "difficulty": difficulty,
                    "language": quiz_language,
                    "mode": mode,
                    "total_score": 0,
                    "previous_questions": "[]"
                })
            )

        elif text.upper() in ["A", "B", "C", "D"]:
            answer = text.upper()

            response = table.get_item(Key={'chat_id': chat_id})
            session = response.get('Item')

            if not session or 'questions' not in session:
                send_message(token, chat_id,
                    "Please send me a file first to start a quiz!",
                    reply_markup=main_menu())
                return {"statusCode": 200, "body": "OK"}

            questions = json.loads(session['questions'])
            current = int(session.get('question_current', 0))
            score = int(session.get('score', 0))
            question = questions[current]
            correct = question["answer"]
            explanation = question["explanation"]

            if answer == correct:
                score += 1
                send_message(token, chat_id,
                    f"Correct! Well done! 🎉\n\nExplanation: {explanation}\n\nScore so far: {score} out of {current + 1}",
                    reply_markup=quiz_menu())
            else:
                send_message(token, chat_id,
                    f"Wrong! The correct answer is {correct}.\n\nExplanation: {explanation}\n\nScore so far: {score} out of {current + 1}",
                    reply_markup=quiz_menu())

            current += 1

            if current >= len(questions):
                difficulty = session.get('quiz_difficulty', 'Easy')
                total_score = int(session.get('total_score', 0)) + score
                all_questions = session.get('questions', '[]')

                if difficulty == 'Easy':
                    keyboard = json.dumps({
                        "keyboard": [[{"text": "Yes!"}, {"text": "No thanks"}]],
                        "one_time_keyboard": True,
                        "resize_keyboard": True
                    })
                    send_message(token, chat_id,
                        f"Easy quiz complete! 🎊\n\nYour score: {score} out of {len(questions)}\n\nReady to try Medium difficulty with the same file?",
                        reply_markup=keyboard)
                    table.update_item(
                        Key={'chat_id': chat_id},
                        UpdateExpression='SET waiting_for = :w, total_score = :t, saved_file_id = :f, saved_file_name = :n, previous_questions = :p',
                        ExpressionAttributeValues={
                            ':w': 'medium_confirm',
                            ':t': total_score,
                            ':f': session.get('file_id', session.get('saved_file_id', '')),
                            ':n': session.get('file_name', session.get('saved_file_name', '')),
                            ':p': all_questions
                        }
                    )

                elif difficulty == 'Medium':
                    keyboard = json.dumps({
                        "keyboard": [[{"text": "Yes!"}, {"text": "No thanks"}]],
                        "one_time_keyboard": True,
                        "resize_keyboard": True
                    })
                    send_message(token, chat_id,
                        f"Medium quiz complete! 🎊\n\nYour score: {score} out of {len(questions)}\n\nReady for the Hard difficulty challenge?",
                        reply_markup=keyboard)

                    existing_previous = session.get('previous_questions', '[]')
                    try:
                        prev_list = json.loads(existing_previous)
                        curr_list = json.loads(all_questions)
                        combined = json.dumps(prev_list + curr_list)
                    except:
                        combined = all_questions

                    table.update_item(
                        Key={'chat_id': chat_id},
                        UpdateExpression='SET waiting_for = :w, total_score = :t, saved_file_id = :f, saved_file_name = :n, previous_questions = :p',
                        ExpressionAttributeValues={
                            ':w': 'hard_confirm',
                            ':t': total_score,
                            ':f': session.get('file_id', session.get('saved_file_id', '')),
                            ':n': session.get('file_name', session.get('saved_file_name', '')),
                            ':p': combined
                        }
                    )

                elif difficulty == 'Hard':
                    send_message(token, chat_id,
                        f"Hard quiz complete! 🏆\n\nYour score: {score} out of {len(questions)}\n\nTotal score across all difficulties: {total_score} out of 30!\n\nAmazing work! Send me another file to start again.",
                        reply_markup=main_menu())
                    table.delete_item(Key={'chat_id': chat_id})

            else:
                table.update_item(
                    Key={'chat_id': chat_id},
                    UpdateExpression='SET question_current = :c, score = :s',
                    ExpressionAttributeValues={':c': current, ':s': score}
                )
                next_question = questions[current]
                text = f"Question {current + 1} of {len(questions)} ({session.get('quiz_difficulty', 'Easy')}):\n\n"
                text += f"{next_question['question']}\n\n"
                for option in next_question["options"]:
                    text += f"{option}\n"
                text += "\nReply with A, B, C or D"
                send_message(token, chat_id, text, reply_markup=quiz_menu())

        else:
            send_message(token, chat_id,
                "Use the menu below to get started! 👇",
                reply_markup=main_menu())

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

    return {"statusCode": 200, "body": "OK"}