import os
import anthropic
import json

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def generate_questions(text: str, difficulty: str = "Easy", language: str = "English", previous_questions: str = "[]") -> list:
    if difficulty == "Easy":
        difficulty_instruction = "Generate EASY questions. Focus on basic facts. Questions should be straightforward."
    elif difficulty == "Hard":
        difficulty_instruction = "Generate HARD questions. Focus on deep understanding and analysis. Questions should be very challenging."
    else:
        difficulty_instruction = "Generate MEDIUM difficulty questions. Mix of straightforward and analytical questions."

    if language == "Amharic":
        language_instruction = """Generate everything in Amharic (አማርኛ). 
Use natural, conversational Amharic that Ethiopians actually speak in daily life.
Use the Ethiopic script (Ge'ez alphabet) throughout.
Make the language warm, friendly and encouraging - like a teacher talking to a student.
Avoid overly formal or academic Amharic. Use everyday spoken Amharic."""
    else:
        language_instruction = f"Generate everything in {language}."

    try:
        prev_list = json.loads(previous_questions)
        if prev_list:
            prev_topics = [q.get('question', '')[:100] for q in prev_list]
            avoid_instruction = f"\n\nIMPORTANT: Do NOT repeat or reuse any of these previous questions. Generate completely NEW and DIFFERENT questions that cover other aspects of the text:\n" + "\n".join([f"- {t}" for t in prev_topics[:10]])
        else:
            avoid_instruction = ""
    except:
        avoid_instruction = ""

    prompt = f"""You are a friendly study assistant. Based on the following text, generate 10 multiple choice questions.

Difficulty: {difficulty_instruction}
Language instructions: {language_instruction}{avoid_instruction}

For each question use this EXACT format:
Q: question here
A) option one
B) option two
C) option three
D) option four
Answer: A
Explanation: explain why the answer is correct based on the text

Separate each question with a blank line.

Text:
{text[:3000]}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    return parse_questions(raw)

def generate_flashcards(text: str, language: str = "English") -> list:
    if language == "Amharic":
        language_instruction = """Generate everything in Amharic (አማርኛ).
Use natural, conversational Amharic that Ethiopians actually speak in daily life.
Use the Ethiopic script (Ge'ez alphabet) throughout.
Make the language warm, friendly and encouraging.
Avoid overly formal Amharic. Use everyday spoken Amharic."""
    else:
        language_instruction = f"Generate everything in {language}."

    prompt = f"""You are a friendly study assistant. Based on the following text, generate 10 flashcards.

Language instructions: {language_instruction}

For each flashcard use this EXACT format:
CONCEPT: concept name here
EXPLANATION: detailed explanation here

Separate each flashcard with a blank line.

Text:
{text[:3000]}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    return parse_flashcards(raw)

def parse_questions(raw: str) -> list:
    questions = []
    blocks = raw.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 7:
            question = {
                "question": lines[0].replace("Q: ", ""),
                "options": lines[1:5],
                "answer": lines[5].replace("Answer: ", "").strip(),
                "explanation": lines[6].replace("Explanation: ", "").strip()
            }
            questions.append(question)

    return questions

def parse_flashcards(raw: str) -> list:
    flashcards = []
    blocks = raw.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 2:
            flashcard = {
                "concept": lines[0].replace("CONCEPT: ", "").strip(),
                "explanation": lines[1].replace("EXPLANATION: ", "").strip()
            }
            flashcards.append(flashcard)

    return flashcards