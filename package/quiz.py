import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_questions(text: str) -> list:
    prompt = f"""You are a study assistant. Based on the following text, generate 10 multiple choice questions to quiz the student.

For each question follow this exact format:
Q: question here
A) option one
B) option two
C) option three
D) option four
Answer: A
Explanation: explain here why the answer is correct based on the text

Here is the text:
{text[:3000]}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw = message.content[0].text
    questions = parse_questions(raw)
    return questions


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
