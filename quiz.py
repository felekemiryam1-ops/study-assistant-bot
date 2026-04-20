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
            prev_topics = [q.get('question', '')[:80] for q in prev_list[:10]]
            avoid_instruction = f"\n\nIMPORTANT: Generate completely NEW and DIFFERENT questions. Do NOT repeat these topics:\n" + \
                "\n".join([f"- {t}" for t in prev_topics])
        else:
            avoid_instruction = ""
    except:
        avoid_instruction = ""

    prompt = f"""You are a friendly study assistant. Based on the following text, generate 10 multiple choice questions.

Difficulty: {difficulty_instruction}
Language: {language_instruction}{avoid_instruction}

Use this EXACT format for each question:
Q: question here
A) option one
B) option two
C) option three
D) option four
Answer: A
Explanation: explain why the answer is correct

Separate each question with one blank line.

Text:
{text[:3000]}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    print(f"Raw response preview: {raw[:200]}")
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

Language: {language_instruction}

Use this EXACT format for each flashcard:
CONCEPT: concept name here
EXPLANATION: detailed explanation here

Separate each flashcard with one blank line.

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
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]

        question_line = None
        options = []
        answer_line = None
        explanation_line = None

        for line in lines:
            if line.startswith("Q:"):
                question_line = line.replace("Q:", "").strip()
            elif line.startswith("A)") or line.startswith("B)") or line.startswith("C)") or line.startswith("D)"):
                options.append(line)
            elif line.startswith("Answer:"):
                answer_line = line.replace("Answer:", "").strip()
            elif line.startswith("Explanation:"):
                explanation_line = line.replace("Explanation:", "").strip()

        if question_line and len(options) == 4 and answer_line and explanation_line:
            questions.append({
                "question": question_line,
                "options": options,
                "answer": answer_line[0] if answer_line else "A",
                "explanation": explanation_line
            })

    return questions


def parse_flashcards(raw: str) -> list:
    flashcards = []
    blocks = raw.strip().split("\n\n")

    for block in blocks:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]

        concept_line = None
        explanation_line = None

        for line in lines:
            if line.startswith("CONCEPT:"):
                concept_line = line.replace("CONCEPT:", "").strip()
            elif line.startswith("EXPLANATION:"):
                explanation_line = line.replace("EXPLANATION:", "").strip()

        if concept_line and explanation_line:
            flashcards.append({
                "concept": concept_line,
                "explanation": explanation_line
            })

    return flashcards
