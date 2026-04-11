import streamlit as st
import sqlite3
import hashlib
import random
import time
import os

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="🎯 Online Quiz App",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f0f1a; }
    .stApp { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%); }

    .quiz-header {
        text-align: center;
        padding: 2rem 1rem 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102,126,234,0.3);
    }
    .quiz-header h1 { color: white; font-size: 2.2rem; margin: 0; }
    .quiz-header p  { color: rgba(255,255,255,0.85); margin: 0.3rem 0 0; font-size: 1rem; }

    .card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    .question-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15));
        border: 1px solid rgba(102,126,234,0.4);
        border-radius: 14px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
    }
    .question-text { color: white; font-size: 1.15rem; font-weight: 600; line-height: 1.5; }

    .timer-bar {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        height: 8px;
        margin: 0.5rem 0 1rem;
        overflow: hidden;
    }

    .result-correct {
        background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(16,185,129,0.2));
        border: 1px solid rgba(34,197,94,0.4);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.4rem 0;
        color: #4ade80;
    }
    .result-wrong {
        background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(220,38,38,0.2));
        border: 1px solid rgba(239,68,68,0.4);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.4rem 0;
        color: #f87171;
    }

    .leaderboard-row {
        background: rgba(255,255,255,0.04);
        border-radius: 8px;
        padding: 0.7rem 1rem;
        margin: 0.3rem 0;
        display: flex;
        justify-content: space-between;
        color: #e2e8f0;
    }
    .rank-gold   { color: #fbbf24; font-weight: bold; font-size: 1.1rem; }
    .rank-silver { color: #94a3b8; font-weight: bold; }
    .rank-bronze { color: #b45309; font-weight: bold; }

    div[data-testid="stRadio"] label {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        margin: 0.3rem 0 !important;
        color: white !important;
        transition: all 0.2s;
        display: block;
        cursor: pointer;
    }
    div[data-testid="stRadio"] label:hover {
        background: rgba(102,126,234,0.25) !important;
        border-color: rgba(102,126,234,0.6) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100%;
        transition: all 0.2s;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(102,126,234,0.5) !important;
    }

    .stTextInput > div > input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 0.6rem 1rem !important;
    }
    .stTextInput > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102,126,234,0.3) !important;
    }

    .stat-box {
        background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2));
        border: 1px solid rgba(102,126,234,0.35);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .stat-box .value { font-size: 2rem; font-weight: 800; color: #a78bfa; }
    .stat-box .label { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }

    h2, h3 { color: #e2e8f0 !important; }
    p, li   { color: #cbd5e1; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# DATABASE — SQLite (works on Streamlit Cloud)
# ──────────────────────────────────────────────
DB_PATH = "quiz_app.db"

QUESTIONS_PER_QUIZ = 5
TIME_PER_QUESTION  = 15  # seconds

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category_id INTEGER,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)     REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
    """)

    # Seed categories & questions once
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        cats = ["Python", "General Knowledge", "Mathematics"]
        c.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", [(x,) for x in cats])
        conn.commit()

        c.execute("SELECT id, name FROM categories")
        cat_map = {name: cid for cid, name in c.fetchall()}

        questions = [
            # Python
            (cat_map["Python"], "What is the output of type([])?", "<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>", "A"),
            (cat_map["Python"], "Which keyword is used to define a function in Python?", "func", "def", "function", "define", "B"),
            (cat_map["Python"], "What does len('hello') return?", "4", "5", "6", "Error", "B"),
            (cat_map["Python"], "Which of these is a mutable data type?", "tuple", "string", "list", "int", "C"),
            (cat_map["Python"], "What is used to handle exceptions in Python?", "try/except", "catch/throw", "error/handle", "check/fix", "A"),
            (cat_map["Python"], "Which operator is used for floor division?", "/", "//", "%", "**", "B"),
            (cat_map["Python"], "What does 'pip' stand for?", "Python Install Package", "Pip Installs Packages", "Python Import Package", "Package Install Python", "B"),
            (cat_map["Python"], "How do you start a comment in Python?", "//", "/*", "#", "--", "C"),
            # General Knowledge
            (cat_map["General Knowledge"], "What is the capital of France?", "London", "Berlin", "Paris", "Madrid", "C"),
            (cat_map["General Knowledge"], "How many continents are there on Earth?", "5", "6", "7", "8", "C"),
            (cat_map["General Knowledge"], "Who invented the telephone?", "Thomas Edison", "Nikola Tesla", "Alexander Graham Bell", "Albert Einstein", "C"),
            (cat_map["General Knowledge"], "Which planet is known as the Red Planet?", "Jupiter", "Venus", "Saturn", "Mars", "D"),
            (cat_map["General Knowledge"], "What is the largest ocean on Earth?", "Atlantic", "Indian", "Arctic", "Pacific", "D"),
            (cat_map["General Knowledge"], "How many days are in a leap year?", "365", "366", "364", "367", "B"),
            (cat_map["General Knowledge"], "Which country is the largest by area?", "USA", "China", "Russia", "Canada", "C"),
            (cat_map["General Knowledge"], "Who wrote 'Romeo and Juliet'?", "Charles Dickens", "William Shakespeare", "Mark Twain", "Homer", "B"),
            # Mathematics
            (cat_map["Mathematics"], "What is the value of Pi (approx)?", "3.14", "2.17", "1.61", "3.41", "A"),
            (cat_map["Mathematics"], "What is 12 x 12?", "124", "136", "144", "148", "C"),
            (cat_map["Mathematics"], "What is the square root of 144?", "11", "12", "13", "14", "B"),
            (cat_map["Mathematics"], "What is 25% of 200?", "25", "40", "50", "75", "C"),
            (cat_map["Mathematics"], "Solve: 5! (5 factorial)", "60", "100", "120", "150", "C"),
            (cat_map["Mathematics"], "What is the sum of angles in a triangle?", "90°", "180°", "270°", "360°", "B"),
            (cat_map["Mathematics"], "What is 2 to the power of 10?", "512", "1024", "2048", "256", "B"),
            (cat_map["Mathematics"], "Which is a prime number?", "9", "15", "21", "17", "D"),
        ]
        c.executemany("""
            INSERT INTO questions
            (category_id,question,option_a,option_b,option_c,option_d,correct_option)
            VALUES (?,?,?,?,?,?,?)
        """, questions)
        conn.commit()
    conn.close()

# ──────────────────────────────────────────────
# AUTH HELPERS
# ──────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username, password):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hash_pw(password)))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return {"id": user_id, "username": username}, None
    except sqlite3.IntegrityError:
        return None, "Username already taken. Choose another."

def login_user(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE username=? AND password=?",
              (username, hash_pw(password)))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "username": row["username"]}, None
    return None, "Invalid username or password."

# ──────────────────────────────────────────────
# QUIZ HELPERS
# ──────────────────────────────────────────────
def get_categories():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM categories")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def fetch_questions(category_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT * FROM questions WHERE category_id=?
                 ORDER BY RANDOM() LIMIT ?""",
              (category_id, QUESTIONS_PER_QUIZ))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def save_score(user_id, category_id, score, total):
    pct = (score / total) * 100
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO scores (user_id,category_id,score,total,percentage)
                 VALUES (?,?,?,?,?)""",
              (user_id, category_id, score, total, pct))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT u.username, ca.name AS category,
               s.score, s.total, s.percentage,
               strftime('%d %b %Y %H:%M', s.played_at) AS played_on
        FROM scores s
        JOIN users u    ON s.user_id     = u.id
        JOIN categories ca ON s.category_id = ca.id
        ORDER BY s.percentage DESC, s.played_at DESC
        LIMIT 10
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_history(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT ca.name AS category, s.score, s.total, s.percentage,
               strftime('%d %b %Y %H:%M', s.played_at) AS played_on
        FROM scores s
        JOIN categories ca ON s.category_id = ca.id
        WHERE s.user_id = ?
        ORDER BY s.played_at DESC
    """, (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def grade_label(pct):
    if pct == 100: return "🏆 PERFECT!"
    if pct >= 80:  return "🥇 Excellent!"
    if pct >= 60:  return "🥈 Good Job!"
    if pct >= 40:  return "🥉 Keep Practicing!"
    return "📚 Needs More Study"

# ──────────────────────────────────────────────
# SESSION STATE INIT
# ──────────────────────────────────────────────
def ss_init():
    defaults = {
        "page":        "auth",   # auth | home | category | quiz | results | leaderboard | history
        "auth_mode":   "login",  # login | register
        "user":        None,
        "category":    None,
        "questions":   [],
        "q_index":     0,
        "score":       0,
        "review":      [],
        "start_time":  None,
        "answer_given": False,
        "last_answer": None,
        "last_correct": None,
        "elapsed":     0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
def render_header(subtitle=""):
    st.markdown(f"""
    <div class="quiz-header">
        <h1>🎯 Online Quiz App</h1>
        <p>{subtitle if subtitle else "Test your knowledge across multiple categories"}</p>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# PAGE: AUTH
# ══════════════════════════════════════════════
def page_auth():
    render_header()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_reg = st.tabs(["🔐 Login", "📝 Register"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            uname = st.text_input("Username", key="li_user", placeholder="Enter your username")
            pwd   = st.text_input("Password", type="password", key="li_pwd", placeholder="Enter your password")
            if st.button("Login →", key="btn_login"):
                if not uname or not pwd:
                    st.error("Please fill in all fields.")
                else:
                    user, err = login_user(uname, pwd)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.user = user
                        st.session_state.page = "home"
                        st.rerun()

        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            uname2 = st.text_input("Choose Username", key="rg_user", placeholder="Pick a unique username")
            pwd2   = st.text_input("Choose Password", type="password", key="rg_pwd", placeholder="At least 4 characters")
            if st.button("Create Account →", key="btn_reg"):
                if not uname2 or not pwd2:
                    st.error("Please fill in all fields.")
                elif len(pwd2) < 4:
                    st.error("Password must be at least 4 characters.")
                else:
                    user, err = register_user(uname2, pwd2)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.user = user
                        st.session_state.page = "home"
                        st.success(f"Welcome, {user['username']}! 🎉")
                        time.sleep(0.8)
                        st.rerun()

# ══════════════════════════════════════════════
# PAGE: HOME MENU
# ══════════════════════════════════════════════
def page_home():
    user = st.session_state.user
    render_header(f"Welcome back, {user['username']}! 👋")

    # Quick stats
    history = get_history(user["id"])
    total_games = len(history)
    avg_pct     = round(sum(r["percentage"] for r in history) / total_games, 1) if history else 0
    best_pct    = round(max(r["percentage"] for r in history), 1) if history else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="value">{total_games}</div><div class="label">Games Played</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="value">{avg_pct}%</div><div class="label">Average Score</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="value">{best_pct}%</div><div class="label">Best Score</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Start Quiz"):
            st.session_state.page = "category"
            st.rerun()
    with col2:
        if st.button("🏆 Leaderboard"):
            st.session_state.page = "leaderboard"
            st.rerun()

    col3, col4 = st.columns(2)
    with col3:
        if st.button("📊 My History"):
            st.session_state.page = "history"
            st.rerun()
    with col4:
        if st.button("🚪 Logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ══════════════════════════════════════════════
# PAGE: CATEGORY SELECT
# ══════════════════════════════════════════════
def page_category():
    render_header("Choose a Category")
    categories = get_categories()

    cat_icons = {"Python": "🐍", "General Knowledge": "🌍", "Mathematics": "🔢"}

    cols = st.columns(len(categories))
    for i, cat in enumerate(categories):
        with cols[i]:
            icon = cat_icons.get(cat["name"], "📚")
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2.5rem;">{icon}</div>
                <h3 style="color:white;margin:0.5rem 0;">{cat['name']}</h3>
                <p style="color:#94a3b8;font-size:0.85rem;">{QUESTIONS_PER_QUIZ} questions · {TIME_PER_QUESTION}s each</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Play {cat['name']}", key=f"cat_{cat['id']}"):
                qs = fetch_questions(cat["id"])
                st.session_state.category     = cat
                st.session_state.questions    = qs
                st.session_state.q_index      = 0
                st.session_state.score        = 0
                st.session_state.review       = []
                st.session_state.start_time   = time.time()
                st.session_state.answer_given = False
                st.session_state.last_answer  = None
                st.session_state.last_correct = None
                st.session_state.page         = "quiz"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Menu"):
        st.session_state.page = "home"
        st.rerun()

# ══════════════════════════════════════════════
# PAGE: QUIZ
# ══════════════════════════════════════════════
def page_quiz():
    questions = st.session_state.questions
    idx       = st.session_state.q_index

    if idx >= len(questions):
        # Save & go to results
        save_score(
            st.session_state.user["id"],
            st.session_state.category["id"],
            st.session_state.score,
            len(questions),
        )
        st.session_state.page = "results"
        st.rerun()

    q = questions[idx]

    # ── Timer ──
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, TIME_PER_QUESTION - elapsed)
    pct_left  = remaining / TIME_PER_QUESTION

    # Auto-advance on timeout
    if elapsed > TIME_PER_QUESTION and not st.session_state.answer_given:
        st.session_state.answer_given = True
        st.session_state.last_answer  = None
        st.session_state.last_correct = q["correct_option"]
        st.session_state.review.append({
            "question":   q["question"],
            "your_answer": "⏰ Timed Out",
            "correct":    q["correct_option"],
            "is_correct": False,
        })

    render_header(f"{st.session_state.category['name']} Quiz")

    # Progress
    st.markdown(f"**Question {idx + 1} of {len(questions)}**")
    st.progress((idx) / len(questions))

    # Timer bar
    bar_color = "#22c55e" if pct_left > 0.5 else "#f59e0b" if pct_left > 0.25 else "#ef4444"
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
        <div style="flex:1; background:rgba(255,255,255,0.1); border-radius:8px; height:10px; overflow:hidden;">
            <div style="width:{pct_left*100:.1f}%; height:100%; background:{bar_color}; border-radius:8px; transition:width 0.3s;"></div>
        </div>
        <span style="color:{bar_color}; font-weight:bold; min-width:40px;">⏱ {remaining:.0f}s</span>
    </div>
    """, unsafe_allow_html=True)

    # Question card
    opt_map = {"A": q["option_a"], "B": q["option_b"], "C": q["option_c"], "D": q["option_d"]}
    st.markdown(f'<div class="question-card"><p class="question-text">Q{idx+1}. {q["question"]}</p></div>', unsafe_allow_html=True)

    if not st.session_state.answer_given:
        choice = st.radio(
            "Select your answer:",
            options=["A", "B", "C", "D"],
            format_func=lambda x: f"{x})  {opt_map[x]}",
            key=f"q_{idx}",
            index=None,
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ Submit Answer", key=f"submit_{idx}"):
                if choice is None:
                    st.warning("Please select an answer first!")
                else:
                    is_correct = (choice == q["correct_option"])
                    if is_correct:
                        st.session_state.score += 1
                    st.session_state.answer_given = True
                    st.session_state.last_answer  = choice
                    st.session_state.last_correct = q["correct_option"]
                    st.session_state.review.append({
                        "question":    q["question"],
                        "your_answer": choice,
                        "correct":     q["correct_option"],
                        "is_correct":  is_correct,
                    })
                    st.rerun()
        with col2:
            # Auto-refresh for timer
            if remaining > 0:
                time.sleep(0.5)
                st.rerun()

    else:
        # Show feedback
        ans   = st.session_state.last_answer
        corr  = st.session_state.last_correct
        is_ok = (ans == corr)

        if is_ok:
            st.markdown(f'<div class="result-correct">✅ Correct! The answer is <strong>{corr}) {opt_map[corr]}</strong></div>', unsafe_allow_html=True)
        elif ans == "⏰ Timed Out" or ans is None:
            st.markdown(f'<div class="result-wrong">⏰ Time\'s up! Correct answer: <strong>{corr}) {opt_map[corr]}</strong></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-wrong">❌ Wrong! You chose <strong>{ans}) {opt_map[ans]}</strong>. Correct: <strong>{corr}) {opt_map[corr]}</strong></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        btn_label = "Next Question →" if idx + 1 < len(questions) else "See Results 🏁"
        if st.button(btn_label, key=f"next_{idx}"):
            st.session_state.q_index      += 1
            st.session_state.answer_given  = False
            st.session_state.last_answer   = None
            st.session_state.last_correct  = None
            st.session_state.start_time    = time.time()
            st.rerun()

# ══════════════════════════════════════════════
# PAGE: RESULTS
# ══════════════════════════════════════════════
def page_results():
    user     = st.session_state.user
    category = st.session_state.category
    score    = st.session_state.score
    total    = len(st.session_state.questions)
    review   = st.session_state.review
    pct      = (score / total) * 100

    render_header("Quiz Complete!")

    # Score card
    grade = grade_label(pct)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stat-box"><div class="value">{score}/{total}</div><div class="label">Score</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-box"><div class="value">{pct:.0f}%</div><div class="label">Percentage</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-box"><div class="value">{grade}</div><div class="label">Grade</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Question Review")

    for i, r in enumerate(review, 1):
        if r["is_correct"]:
            st.markdown(f'<div class="result-correct">✅ <strong>Q{i}.</strong> {r["question"][:70]}{"..." if len(r["question"])>70 else ""}<br><small>Your answer: {r["your_answer"]} ✓</small></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-wrong">❌ <strong>Q{i}.</strong> {r["question"][:70]}{"..." if len(r["question"])>70 else ""}<br><small>Your answer: {r["your_answer"]} | Correct: {r["correct"]}</small></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Play Again"):
            st.session_state.page = "category"
            st.rerun()
    with col2:
        if st.button("🏠 Home"):
            st.session_state.page = "home"
            st.rerun()

# ══════════════════════════════════════════════
# PAGE: LEADERBOARD
# ══════════════════════════════════════════════
def page_leaderboard():
    render_header("🏆 Top 10 Leaderboard")
    rows = get_leaderboard()

    if not rows:
        st.info("No scores yet — be the first to play!")
    else:
        rank_styles = ["rank-gold", "rank-silver", "rank-bronze"]
        rank_emojis = ["🥇", "🥈", "🥉"]

        for i, r in enumerate(rows, 1):
            rs   = rank_styles[i-1] if i <= 3 else ""
            em   = rank_emojis[i-1] if i <= 3 else f"#{i}"
            col1, col2, col3, col4, col5 = st.columns([1, 2.5, 2.5, 1.5, 2])
            with col1: st.markdown(f'<span class="{rs}">{em}</span>', unsafe_allow_html=True)
            with col2: st.markdown(f"**{r['username']}**")
            with col3: st.markdown(f"_{r['category']}_")
            with col4: st.markdown(f"{r['score']}/{r['total']}")
            with col5: st.markdown(f"`{r['percentage']:.1f}%`")
            st.divider()

    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()

# ══════════════════════════════════════════════
# PAGE: MY HISTORY
# ══════════════════════════════════════════════
def page_history():
    user = st.session_state.user
    render_header(f"📊 {user['username']}'s Quiz History")
    rows = get_history(user["id"])

    if not rows:
        st.info("You haven't played any quiz yet! Start one now.")
    else:
        for i, r in enumerate(rows, 1):
            pct   = r["percentage"]
            color = "#22c55e" if pct >= 60 else "#f59e0b" if pct >= 40 else "#ef4444"
            st.markdown(f"""
            <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong style="color:white;">#{i} — {r['category']}</strong><br>
                    <small style="color:#94a3b8;">{r['played_on']}</small>
                </div>
                <div style="text-align:right;">
                    <strong style="color:{color}; font-size:1.2rem;">{pct:.1f}%</strong><br>
                    <small style="color:#94a3b8;">{r['score']}/{r['total']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()

# ──────────────────────────────────────────────
# ROUTER
# ──────────────────────────────────────────────
def main():
    init_db()
    ss_init()

    page = st.session_state.page

    # Guard: unauthenticated users only see auth
    if page != "auth" and st.session_state.user is None:
        st.session_state.page = "auth"
        page = "auth"

    if   page == "auth":        page_auth()
    elif page == "home":        page_home()
    elif page == "category":    page_category()
    elif page == "quiz":        page_quiz()
    elif page == "results":     page_results()
    elif page == "leaderboard": page_leaderboard()
    elif page == "history":     page_history()

if __name__ == "__main__":
    main()

