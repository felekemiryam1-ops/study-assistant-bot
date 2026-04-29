import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from extractor import extract_text
from quiz import generate_questions, generate_flashcards

st.set_page_config(
    page_title="YeTemare — AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(
    """
<style>
    /* Global */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #f8f9fa;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hero section */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 60px 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        text-align: center;
        color: white;
    }
    
    .hero h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 10px;
        letter-spacing: -1px;
    }
    
    .hero p {
        font-size: 1.2rem;
        opacity: 0.8;
        margin-bottom: 5px;
    }
    
    .hero-amharic {
        font-size: 1rem;
        opacity: 0.6;
        font-style: italic;
    }
    
    /* Stats cards */
    .stat-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #eee;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0f3460;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Upload area */
    .upload-section {
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #eee;
        margin-bottom: 20px;
    }
    
    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Question card */
    .question-card {
        background: white;
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #eee;
        border-left: 4px solid #0f3460;
    }
    
    .question-number {
        font-size: 0.8rem;
        font-weight: 600;
        color: #0f3460;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    
    .question-text {
        font-size: 1.1rem;
        font-weight: 500;
        color: #1a1a2e;
        line-height: 1.6;
    }
    
    /* Results */
    .result-correct {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
    }
    
    .result-wrong {
        background: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
    }
    
    /* Score card */
    .score-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        color: white;
        margin: 20px 0;
    }
    
    .score-big {
        font-size: 5rem;
        font-weight: 700;
        line-height: 1;
    }
    
    .score-label {
        font-size: 1rem;
        opacity: 0.7;
        margin-top: 10px;
    }
    
    /* Leaderboard */
    .leaderboard-row {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    
    .rank-1 { border-left: 4px solid #FFD700; }
    .rank-2 { border-left: 4px solid #C0C0C0; }
    .rank-3 { border-left: 4px solid #CD7F32; }
    
    /* Flashcard */
    .flashcard-front {
        background: linear-gradient(135deg, #0f3460, #1a1a2e);
        border-radius: 20px;
        padding: 50px 40px;
        text-align: center;
        color: white;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .flashcard-back {
        background: white;
        border-radius: 20px;
        padding: 40px;
        border: 2px solid #0f3460;
        min-height: 200px;
    }
    
    /* Progress bar */
    .progress-container {
        background: #eee;
        border-radius: 100px;
        height: 8px;
        margin: 10px 0;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #0f3460, #e94560);
        border-radius: 100px;
        height: 8px;
        transition: width 0.3s ease;
    }
    
    /* Sidebar */
    .sidebar-section {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #eee;
    }

    /* Button override */
    .stButton > button {
        background: linear-gradient(135deg, #1a1a2e, #0f3460);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    
    .stButton > button:hover {
        opacity: 0.9;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)

if "questions" not in st.session_state:
    st.session_state.questions = None
if "flashcards" not in st.session_state:
    st.session_state.flashcards = None
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "mode" not in st.session_state:
    st.session_state.mode = None
if "score_history" not in st.session_state:
    st.session_state.score_history = []
if "flashcard_flipped" not in st.session_state:
    st.session_state.flashcard_flipped = False
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "page" not in st.session_state:
    st.session_state.page = "home"

with st.sidebar:
    st.markdown("### 🎯 YeTemare")
    st.markdown("*የተማረ — The Educated One*")
    st.divider()

    page = st.radio(
        "Navigate",
        ["🏠 Home", "📊 My Progress", "🏆 Leaderboard"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**⚙️ Quiz Settings**")

    difficulty = st.select_slider(
        "Difficulty", options=["Easy", "Medium", "Hard"], value="Easy"
    )

    language = st.selectbox(
        "Language",
        ["English", "Amharic", "French"],
        format_func=lambda x: {
            "English": "🇬🇧 English",
            "Amharic": "🇪🇹 Amharic",
            "French": "🇫🇷 French",
        }[x],
    )

    mode = st.radio(
        "Mode",
        ["Quiz", "Flashcards"],
        format_func=lambda x: "📝 Quiz" if x == "Quiz" else "🃏 Flashcards",
    )

    st.divider()
    st.markdown("**📁 Supported Files**")
    st.markdown("PDF • PowerPoint • Word • Text")

    if st.button("🔄 Reset Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if page == "🏠 Home":

    st.markdown(
        """
    <div class="hero">
        <h1>📚 YeTemare</h1>
        <p>AI-powered study assistant for every Ethiopian student</p>
        <p class="hero-amharic">ማንኛውም ርዕሰ ጉዳይ · ማንኛውም ቋንቋ · ማንኛውም ቦታ</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    total_quizzes = len(st.session_state.score_history)
    avg_score = (
        sum([s["percentage"] for s in st.session_state.score_history]) / total_quizzes
        if total_quizzes > 0
        else 0
    )
    best_score = (
        max([s["percentage"] for s in st.session_state.score_history])
        if total_quizzes > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-number">{total_quizzes}</div>
            <div class="stat-label">Quizzes Taken</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-number">{avg_score:.0f}%</div>
            <div class="stat-label">Average Score</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-number">{best_score:.0f}%</div>
            <div class="stat-label">Best Score</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-number">{total_quizzes * 10}</div>
            <div class="stat-label">Questions Answered</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your study file here",
        type=["pdf", "pptx", "docx", "txt"],
        help="Upload any study material — PDF, PowerPoint, Word or Text",
    )

    if uploaded_file:
        st.success(f"✅ **{uploaded_file.name}** ready to process")

        col1, col2 = st.columns([3, 1])
        with col1:
            generate_btn = st.button(
                f"🚀 Generate {'Flashcards' if mode == 'Flashcards' else 'Quiz'} — {difficulty} · {language}",
                type="primary",
            )

        if generate_btn:
            for key in [
                "questions",
                "flashcards",
                "answers",
                "submitted",
                "mode",
                "flashcard_flipped",
                "flashcard_index",
            ]:
                if key in st.session_state:
                    del st.session_state[key]

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
            ) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            with st.spinner("📖 Reading your file..."):
                text_content = extract_text(tmp_path)

            if not text_content.strip():
                st.error("Could not extract text. Please try another file.")
            else:
                if mode == "Flashcards":
                    with st.spinner(f"🃏 Creating flashcards in {language}..."):
                        st.session_state.flashcards = generate_flashcards(
                            text_content, language
                        )
                        st.session_state.mode = "Flashcards"
                        st.session_state.flashcard_index = 0
                        st.session_state.flashcard_flipped = False
                else:
                    with st.spinner(
                        f"🤖 Generating {difficulty} questions in {language}..."
                    ):
                        st.session_state.questions = generate_questions(
                            text_content, difficulty, language
                        )
                        st.session_state.mode = "Quiz"
                        st.session_state.difficulty = difficulty
                        st.session_state.language = language
                st.rerun()

    if st.session_state.mode == "Flashcards" and st.session_state.flashcards:
        flashcards = st.session_state.flashcards
        idx = st.session_state.flashcard_index
        card = flashcards[idx]

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**🃏 Flashcard {idx + 1} of {len(flashcards)}**")

        progress_pct = int((idx / len(flashcards)) * 100)
        st.markdown(
            f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress_pct}%"></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if not st.session_state.flashcard_flipped:
            st.markdown(
                f"""
            <div class="flashcard-front">
                <p style="opacity:0.6; font-size:0.85rem; margin-bottom:20px">CONCEPT</p>
                <h2 style="font-size:1.8rem; font-weight:600">{card['concept']}</h2>
                <p style="opacity:0.5; margin-top:30px; font-size:0.85rem">👆 Click to reveal answer</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            if st.button("👆 Flip Card"):
                st.session_state.flashcard_flipped = True
                st.rerun()
        else:
            st.markdown(
                f"""
            <div class="flashcard-back">
                <p style="color:#0f3460; font-weight:600; font-size:0.85rem; margin-bottom:15px">✅ ANSWER</p>
                <p style="font-size:1.1rem; line-height:1.7; color:#1a1a2e">{card['explanation']}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("➡️ Next Card"):
                    if idx + 1 >= len(flashcards):
                        st.success("🎊 You completed all flashcards!")
                        st.session_state.flashcards = None
                        st.session_state.mode = None
                    else:
                        st.session_state.flashcard_index += 1
                        st.session_state.flashcard_flipped = False
                    st.rerun()
            with col2:
                if st.button("⏭️ Skip"):
                    if idx + 1 >= len(flashcards):
                        st.session_state.flashcards = None
                        st.session_state.mode = None
                    else:
                        st.session_state.flashcard_index += 1
                        st.session_state.flashcard_flipped = False
                    st.rerun()

    elif st.session_state.mode == "Quiz" and st.session_state.questions:
        questions = st.session_state.questions
        difficulty = st.session_state.get("difficulty", "Easy")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 📝 Quiz — {difficulty} Level")
        st.markdown(f"*{len(questions)} questions from your file*")

        for i, question in enumerate(questions):
            st.markdown(
                f"""
            <div class="question-card">
                <div class="question-number">Question {i+1} of {len(questions)}</div>
                <div class="question-text">{question['question']}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            answer = st.radio(
                f"q{i}",
                question["options"],
                key=f"q_{i}",
                index=None,
                label_visibility="collapsed",
            )

            if answer:
                st.session_state.answers[i] = answer[0]

        answered = len(st.session_state.answers)
        st.markdown(f"*{answered} of {len(questions)} answered*")

        if not st.session_state.submitted:
            if st.button("✅ Submit Answers", type="primary"):
                st.session_state.submitted = True
                st.rerun()

        if st.session_state.submitted:
            score = 0
            st.markdown("---")
            st.markdown("## 📊 Results")

            for i, question in enumerate(questions):
                user_answer = st.session_state.answers.get(i, "")
                correct = question["answer"]
                is_correct = user_answer == correct

                if is_correct:
                    score += 1
                    st.markdown(
                        f"""
                    <div class="result-correct">
                        ✅ <strong>Question {i+1}: Correct!</strong>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                    <div class="result-wrong">
                        ❌ <strong>Question {i+1}: Wrong</strong> — Correct answer: <strong>{correct}</strong>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                with st.expander(f"📖 Explanation for Question {i+1}"):
                    st.write(question["explanation"])

            percentage = (score / len(questions)) * 100

            st.session_state.score_history.append(
                {
                    "date": datetime.now().strftime("%b %d, %Y"),
                    "score": score,
                    "total": len(questions),
                    "percentage": percentage,
                    "difficulty": difficulty,
                }
            )

            st.markdown(
                f"""
            <div class="score-card">
                <div class="score-big">{score}/{len(questions)}</div>
                <div class="score-label">{percentage:.0f}% — {difficulty} Level</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if percentage == 100:
                st.balloons()
                st.success("🏆 Perfect score! Incredible!")
            elif percentage >= 70:
                st.success("💪 Great job! Keep it up!")
            elif percentage >= 50:
                st.warning("📖 Good effort! Review and try again!")
            else:
                st.error("💡 Keep studying! You'll get there!")

            share_text = f"I scored {score}/{len(questions)} ({percentage:.0f}%) on a {difficulty} quiz using YeTemare AI Study Assistant! 🎓 Try it at https://yetemare.online"

            st.markdown("**📤 Share your result:**")
            st.code(share_text, language=None)

            if st.button("🔄 Take Another Quiz"):
                for key in ["questions", "flashcards", "answers", "submitted", "mode"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

elif page == "📊 My Progress":
    st.markdown("## 📊 My Progress")

    if not st.session_state.score_history:
        st.info("No quiz history yet. Take a quiz to see your progress!")
    else:
        history = st.session_state.score_history

        total = len(history)
        avg = sum([s["percentage"] for s in history]) / total
        best = max([s["percentage"] for s in history])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Quizzes", total)
        with col2:
            st.metric("Average Score", f"{avg:.0f}%")
        with col3:
            st.metric("Best Score", f"{best:.0f}%")

        st.markdown("### 📈 Quiz History")
        for i, record in enumerate(reversed(history)):
            st.markdown(
                f"""
            <div class="leaderboard-row">
                <div style="flex:1">
                    <strong>{record['date']}</strong> — {record['difficulty']} Level
                </div>
                <div style="font-size:1.3rem; font-weight:700; color:#0f3460">
                    {record['score']}/{record['total']} ({record['percentage']:.0f}%)
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

elif page == "🏆 Leaderboard":
    st.markdown("## 🏆 Leaderboard")
    st.info("🚧 Leaderboard coming soon! Complete more quizzes to be featured here.")

    st.markdown("### 🎯 Your Stats")
    if st.session_state.score_history:
        best = max([s["percentage"] for s in st.session_state.score_history])
        st.markdown(
            f"""
        <div class="score-card">
            <div class="score-big">{best:.0f}%</div>
            <div class="score-label">Your Best Score</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Take a quiz to appear on the leaderboard!")

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.85rem'>"
    "YeTemare · Built with Claude AI & AWS · "
    "<a href='https://t.me/YourBotUsername' style='color:#0f3460'>Telegram Bot</a>"
    "</p>",
    unsafe_allow_html=True,
)
