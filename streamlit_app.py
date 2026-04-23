from quiz import generate_questions, generate_flashcards
from extractor import extract_text
import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()


st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="centered"
)

st.title("📚 AI Study Assistant")
st.subheader("Upload your study material and get quizzed by AI!")

with st.sidebar:
    st.header("⚙️ Settings")

    difficulty = st.radio(
        "🎯 Difficulty",
        ["Easy", "Medium", "Hard"],
        index=0
    )

    language = st.selectbox(
        "🌍 Language",
        ["English", "Amharic", "French"]
    )

    mode = st.radio(
        "📖 Mode",
        ["Quiz", "Flashcards"],
        index=0
    )

    st.divider()
    st.markdown("**Supported files:**")
    st.markdown("• PDF")
    st.markdown("• PowerPoint (.pptx)")
    st.markdown("• Word (.docx)")
    st.markdown("• Text (.txt)")

    if st.button("🔄 Reset"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if 'questions' not in st.session_state:
    st.session_state.questions = None
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = None
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'mode' not in st.session_state:
    st.session_state.mode = None

uploaded_file = st.file_uploader(
    "Upload your study file",
    type=["pdf", "pptx", "docx", "txt"]
)

if uploaded_file is not None:
    st.success(f"✅ File uploaded: {uploaded_file.name}")

    if st.button("🚀 Generate " + ("Flashcards" if mode == "Flashcards" else "Quiz"), type="primary"):

        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.session_state.questions = None
        st.session_state.flashcards = None
        st.session_state.answers = {}
        st.session_state.submitted = False

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        with st.spinner("📖 Extracting text from your file..."):
            text_content = extract_text(tmp_path)

        if not text_content.strip():
            st.error(
                "Sorry I could not extract text from that file. Please try another one.")
        else:
            st.session_state.text_content = text_content

            if mode == "Flashcards":
                with st.spinner(f"🃏 Generating flashcards in {language}..."):
                    st.session_state.flashcards = generate_flashcards(
                        text_content, language)
                    st.session_state.mode = "Flashcards"
            else:
                with st.spinner(f"🤖 Generating {difficulty} questions in {language}..."):
                    st.session_state.questions = generate_questions(
                        text_content, difficulty, language)
                    st.session_state.mode = "Quiz"
                    st.session_state.difficulty = difficulty

        st.rerun()

if st.session_state.mode == "Flashcards" and st.session_state.flashcards:
    flashcards = st.session_state.flashcards
    st.success(f"Generated {len(flashcards)} flashcards!")
    st.divider()

    for i, card in enumerate(flashcards):
        with st.expander(f"🃏 Flashcard {i+1}: {card['concept']}"):
            st.markdown(f"**Concept:** {card['concept']}")
            st.markdown("---")
            st.markdown(f"**Explanation:** {card['explanation']}")

elif st.session_state.mode == "Quiz" and st.session_state.questions:
    questions = st.session_state.questions
    difficulty = st.session_state.get('difficulty', 'Easy')
    st.success(f"Generated {len(questions)} questions!")
    st.divider()

    for i, question in enumerate(questions):
        st.markdown(f"**Question {i+1} of {len(questions)} ({difficulty}):**")
        st.markdown(f"{question['question']}")

        answer = st.radio(
            "Choose your answer:",
            question['options'],
            key=f"q_{i}",
            index=None
        )

        if answer:
            st.session_state.answers[i] = answer[0]

        st.divider()

    if not st.session_state.submitted:
        if st.button("✅ Submit All Answers", type="primary"):
            st.session_state.submitted = True
            st.rerun()

    if st.session_state.submitted:
        score = 0
        st.markdown("## 📊 Results")

        for i, question in enumerate(questions):
            user_answer = st.session_state.answers.get(i, "")
            correct = question["answer"]

            if user_answer == correct:
                score += 1
                st.success(f"✅ Question {i+1}: Correct!")
            else:
                st.error(f"❌ Question {i+1}: Wrong! Correct answer: {correct}")

            with st.expander(f"📖 Explanation for Question {i+1}"):
                st.write(question["explanation"])

        st.divider()
        percentage = (score / len(questions)) * 100
        st.markdown(
            f"## 🏆 Final Score: {score}/{len(questions)} ({percentage:.0f}%)")

        if percentage == 100:
            st.balloons()
            st.success("Perfect score! Amazing! 🎉")
        elif percentage >= 70:
            st.success("Great job! Keep it up! 💪")
        elif percentage >= 50:
            st.warning("Good effort! Review the explanations and try again! 📖")
        else:
            st.error("Keep studying! You'll get there! 💡")

        if st.button("🔄 Try Again"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

st.divider()
st.markdown("*Built with Claude AI, AWS and Streamlit*")
