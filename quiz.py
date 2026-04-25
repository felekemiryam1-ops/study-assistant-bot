import os
import anthropic
import json

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def generate_questions(
    text: str,
    difficulty: str = "Easy",
    language: str = "English",
    previous_questions: str = "[]",
) -> list:
    if difficulty == "Easy":
        difficulty_instruction = """Generate EASY questions.
- Focus on basic facts directly stated in the text
- Questions should have one obviously correct answer
- Wrong options should be clearly different from the correct answer
- Keep questions and answers SHORT and simple"""

    elif difficulty == "Hard":
        difficulty_instruction = """Generate HARD and TRICKY questions.
- Do NOT make questions longer — make them TRICKIER
- Use confusing or similar-looking answer options
- Ask about exceptions, edge cases, or things easily confused
- Test whether the student truly understands, not just memorized
- Wrong options should be plausible and tempting
- Questions should require thinking, not just recalling facts
- Example: instead of "What is X?" ask "Which of the following is NOT true about X?"
- Keep questions SHORT but make the options tricky"""

    else:
        difficulty_instruction = """Generate MEDIUM difficulty questions.
- Mix of factual recall and concept understanding
- Some questions should require connecting two ideas from the text
- Wrong options should be somewhat plausible
- Keep questions clear and concise"""

    if language == "Amharic":
        language_instruction = """Generate in Amharic (አማርኛ) mixed with English medical terms.
Use natural conversational Amharic that Ethiopian medical students actually speak.
Use Ethiopic script (Ge'ez alphabet) for Amharic words.
Sound like a senior Ethiopian doctor teaching a junior student.

GOLDEN RULE: Keep ALL medical terms in English — Ethiopian medical students 
learn medicine in English. Mix English medical terms with Amharic explanation.

Good example:
"Pulp necrosis ማለት የጥርስ ውስጥ ያለው tissue መሞት ነው። 
ይህ trauma ወይም infection ምክንያት ሊሆን ይችላል።"

Keep these ALWAYS in English:
- All anatomical terms: pulp, incisor, molar, canine, premolar
- All procedures: root canal, extraction, crown, splint
- All conditions: abscess, necrosis, luxation, avulsion, intrusion
- All investigations: X-ray, CT scan, MRI, biopsy
- All medications: antibiotics, analgesics, anesthesia
- Specialties: orthodontics, endodontics, periodontics

Use Amharic ONLY for:
- Connecting words: ማለት, ነው, ይሆናል, ምክንያት, ስለዚህ
- Common words: ህመም (pain), ደም (blood), ልጅ (child), ሐኪም (doctor)
- Explanations and context

CORRECT Amharic medical words when needed:
- Tooth = ጥርስ (NOT ጥንት which means ancient!)
- Gum = ድዳ
- Jaw = መንጋጋ
- Bone = አጥንት
- Pain = ህመም
- Bleeding = ደም መፍሰስ
- Swelling = እብጠት
- Treatment = ህክምና
- Patient = ታካሚ
- Child = ልጅ"""

    else:
        language_instruction = f"""Generate everything in {language}.
This is for MEDICAL STUDENTS — use proper medical terminology throughout.
Questions should test clinical knowledge and understanding."""

    try:
        prev_list = json.loads(previous_questions)
        if prev_list:
            prev_topics = [q.get("question", "")[:60] for q in prev_list[:5]]
            avoid_instruction = (
                f"\n\nIMPORTANT: Generate completely NEW and DIFFERENT questions. Do NOT repeat these topics:\n"
                + "\n".join([f"- {t}" for t in prev_topics])
            )
        else:
            avoid_instruction = ""
    except:
        avoid_instruction = ""

    prompt = f"""You are a friendly Ethiopian medical professor helping medical students study.
Based on the following medical text, generate exactly 10 multiple choice questions.

Difficulty instructions:
{difficulty_instruction}

Language: {language_instruction}{avoid_instruction}

Use this EXACT format for EVERY question — no exceptions:
Q: question here
A) option one
B) option two
C) option three
D) option four
Answer: A
Explanation: short clinical explanation why the answer is correct

Separate each question with exactly one blank line.
You MUST generate exactly 10 questions. No more, no less.
Keep explanations SHORT — maximum 1 sentence.
Use proper medical terminology throughout.

Medical text:
{text[:3000]}"""

    if difficulty == "Hard" and language == "Amharic":
        max_tok = 5000
    elif difficulty == "Hard":
        max_tok = 4000
    else:
        max_tok = 3000

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tok,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text
    print(f"Raw response preview: {raw[:200]}")
    return parse_questions(raw)


def generate_flashcards(text: str, language: str = "English") -> list:
    if language == "Amharic":
        language_instruction = """Generate in Amharic (አማርኛ) mixed with English medical terms.
Use natural conversational Amharic that Ethiopian medical students actually speak.
Use Ethiopic script for Amharic words.
Sound like a senior Ethiopian doctor teaching a junior student.

GOLDEN RULE: Keep ALL medical terms in English.
Mix English medical terms with Amharic explanation sentences.

Good example:
"Avulsion ማለት ጥርሱ ሙሉ በሙሉ ከ socket ውጭ መውጣቱ ነው።
በ30 ደቂቃ ውስጥ replant ካልተደረገ prognosis ይበላሻል።"

Keep these ALWAYS in English:
- All anatomical terms: pulp, socket, apex, root, crown
- All conditions: avulsion, luxation, intrusion, extrusion, necrosis
- All procedures: replantation, splinting, root canal, extraction
- All investigations: X-ray, radiograph, vitality test
- All medications: antibiotics, analgesics, fluoride

Use Amharic for connecting words and explanations only.

CORRECT Amharic words:
- Tooth = ጥርስ (NOT ጥንት!)
- Pain = ህመም
- Child = ልጅ
- Treatment = ህክምና
- Patient = ታካሚ
- Bleeding = ደም መፍሰስ"""

    else:
        language_instruction = f"""Generate everything in {language}.
This is for MEDICAL STUDENTS — use proper medical terminology.
Explanations should be clinically accurate and educational."""

    prompt = f"""You are a friendly Ethiopian medical professor helping medical students study.
Based on the following medical text, generate 10 flashcards.

Language: {language_instruction}

Use this EXACT format for each flashcard:
CONCEPT: medical concept or term here
EXPLANATION: clear clinical explanation here

Separate each flashcard with one blank line.
Use proper medical terminology.
Keep explanations concise but clinically accurate.
Maximum 2 sentences per explanation.

Medical text:
{text[:3000]}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
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
            elif (
                line.startswith("A)")
                or line.startswith("B)")
                or line.startswith("C)")
                or line.startswith("D)")
            ):
                options.append(line)
            elif line.startswith("Answer:"):
                answer_line = line.replace("Answer:", "").strip()
            elif line.startswith("Explanation:"):
                explanation_line = line.replace("Explanation:", "").strip()

        if question_line and len(options) == 4 and answer_line:
            if not explanation_line:
                explanation_line = "See the text for more details."
            questions.append(
                {
                    "question": question_line,
                    "options": options,
                    "answer": answer_line[0] if answer_line else "A",
                    "explanation": explanation_line,
                }
            )

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
            flashcards.append(
                {"concept": concept_line, "explanation": explanation_line}
            )

    return flashcards
