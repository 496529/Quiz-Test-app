import mysql.connector
from mysql.connector import Error
import hashlib
import random
import time
import os

# ─────────────────────────────────────────────
#  DATABASE CONFIG  ← Update your password here
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Sambit@123",   # ← Change this
    "database": "quiz_app_db",
}

QUESTIONS_PER_QUIZ = 5
TIME_PER_QUESTION  = 15  # seconds


# ══════════════════════════════════════════════
#  UTILITIES
# ══════════════════════════════════════════════

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def divider(char="─", width=55):
    print(char * width)

def banner():
    clear()
    divider("═")
    print("         🎯  ONLINE QUIZ APPLICATION  🎯")
    divider("═")

def pause():
    input("\n  Press Enter to continue...")


# ══════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════

def register():
    banner()
    print("          📝  REGISTER NEW ACCOUNT\n")
    username = input("  Enter username : ").strip()
    if not username:
        print("  ❌ Username cannot be empty.")
        pause(); return None

    password = input("  Enter password : ").strip()
    if len(password) < 4:
        print("  ❌ Password must be at least 4 characters.")
        pause(); return None

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hash_password(password))
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"\n  ✅ Account created! Welcome, {username}!")
        pause()
        return {"id": user_id, "username": username}
    except Error as e:
        if "Duplicate entry" in str(e):
            print("  ❌ Username already taken. Try another.")
        else:
            print(f"  ❌ Error: {e}")
        pause(); return None
    finally:
        if conn.is_connected():
            cursor.close(); conn.close()


def login():
    banner()
    print("          🔐  LOGIN\n")
    username = input("  Username : ").strip()
    password = input("  Password : ").strip()

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username FROM users WHERE username=%s AND password=%s",
            (username, hash_password(password))
        )
        user = cursor.fetchone()
        if user:
            print(f"\n  ✅ Welcome back, {user['username']}!")
            pause()
            return user
        else:
            print("  ❌ Invalid username or password.")
            pause(); return None
    except Error as e:
        print(f"  ❌ DB Error: {e}")
        pause(); return None
    finally:
        if conn.is_connected():
            cursor.close(); conn.close()


# ══════════════════════════════════════════════
#  CATEGORIES
# ══════════════════════════════════════════════

def get_categories():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM categories")
        return cursor.fetchall()
    except Error as e:
        print(f"  ❌ Error: {e}"); return []
    finally:
        if conn.is_connected():
            cursor.close(); conn.close()


def choose_category():
    categories = get_categories()
    if not categories:
        print("  ❌ No categories found!"); pause(); return None

    banner()
    print("         📂  SELECT A CATEGORY\n")
    for i, cat in enumerate(categories, 1):
        print(f"    [{i}]  {cat['name']}")
    print(f"    [0]  ← Back")
    divider()

    try:
        choice = int(input("  Your choice : "))
        if choice == 0:
            return None
        if 1 <= choice <= len(categories):
            return categories[choice - 1]
        else:
            print("  ❌ Invalid choice."); pause(); return None
    except ValueError:
        print("  ❌ Please enter a number."); pause(); return None


# ══════════════════════════════════════════════
#  QUIZ ENGINE
# ══════════════════════════════════════════════

def fetch_questions(category_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT * FROM questions WHERE category_id = %s
               ORDER BY RAND() LIMIT %s""",
            (category_id, QUESTIONS_PER_QUIZ)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"  ❌ Error: {e}"); return []
    finally:
        if conn.is_connected():
            cursor.close(); conn.close()


def display_question(q_num, total, question):
    banner()
    divider()
    print(f"  Question {q_num}/{total}  |  ⏱  {TIME_PER_QUESTION}s limit")
    divider()
    print(f"\n  {question['question']}\n")
    print(f"    A)  {question['option_a']}")
    print(f"    B)  {question['option_b']}")
    print(f"    C)  {question['option_c']}")
    print(f"    D)  {question['option_d']}")
    divider()


def get_timed_answer():
    """Get user answer within time limit."""
    start = time.time()
    try:
        answer = input("  Your answer (A/B/C/D) : ").strip().upper()
        elapsed = time.time() - start
        if elapsed > TIME_PER_QUESTION:
            print("  ⏰ Time's up!")
            return None, elapsed
        if answer not in ("A", "B", "C", "D"):
            print("  ❌ Invalid input. Marked as wrong.")
            return None, elapsed
        return answer, elapsed
    except KeyboardInterrupt:
        return None, 0


def conduct_quiz(user, category):
    questions = fetch_questions(category["id"])
    if not questions:
        print("  ❌ No questions available for this category.")
        pause(); return

    score       = 0
    review_data = []

    for idx, q in enumerate(questions, 1):
        display_question(idx, len(questions), q)
        answer, elapsed = get_timed_answer()

        is_correct = (answer == q["correct_option"])
        if is_correct:
            score += 1
            feedback = "✅ Correct!"
        else:
            feedback = f"❌ Wrong!  Correct answer: {q['correct_option']}"

        print(f"\n  {feedback}  (answered in {elapsed:.1f}s)")
        review_data.append({
            "question"     : q["question"],
            "your_answer"  : answer,
            "correct"      : q["correct_option"],
            "is_correct"   : is_correct,
        })
        time.sleep(1.2)

    # Save score
    save_score(user["id"], category["id"], score, len(questions))

    # Show results
    show_results(user, category, score, len(questions), review_data)


def save_score(user_id, category_id, score, total):
    percentage = (score / total) * 100
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO scores (user_id, category_id, score, total, percentage)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, category_id, score, total, percentage)
        )
        conn.commit()
    except Error as e:
        print(f"  ❌ Could not save score: {e}")
    finally:
        if conn.is_connected():
            cursor.close(); conn.close()


def show_results(user, category, score, total, review_data):
    banner()
    percentage = (score / total) * 100

    if percentage == 100:
        grade = "🏆 PERFECT!"
    elif percentage >= 80:
        grade = "🥇 Excellent!"
    elif percentage >= 60:
        grade = "🥈 Good Job!"
    elif percentage >= 40:
        grade = "🥉 Keep Practicing!"
    else:
        grade = "📚 Needs More Study"

    print(f"          🎯  QUIZ RESULTS\n")
    print(f"  Player   : {user['username']}")
    print(f"  Category : {category['name']}")
    divider()
    print(f"  Score    : {score} / {total}")
    print(f"  Percent  : {percentage:.1f}%")
    print(f"  Grade    : {grade}")
    divider()

    print("\n  📋 REVIEW:\n")
    for i, r in enumerate(review_data, 1):
        status = "✅" if r["is_correct"] else "❌"
        ans    = r["your_answer"] if r["your_answer"] else "No answer"
        print(f"  {i}. {status}  {r['question'][:50]}...")
        if not r["is_correct"]:
            print(f"       Your: {ans}  |  Correct: {r['correct']}")
    pause()


# ══════════════════════════════════════════════
#  LEADERBOARD
# ══════════════════════════════════════════════

def show_leaderboard():
    banner()
    print("         🏆  TOP SCORES  (All Categories)\n")
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.username, c.name AS category,
                   s.score, s.total, s.percentage,
                   DATE_FORMAT(s.played_at, '%d %b %Y %H:%i') AS played_on
            FROM scores s
            JOIN users u ON s.user_id = u.id
            JOIN categories c ON s.category_id = c.id
            ORDER BY s.percentage DESC, s.played_at DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if not rows:
            print("  No scores yet. Be the first to play!")
        else:
            print(f"  {'#':<3} {'Player':<15} {'Category':<20} {'Score':<8} {'%':<8} {'Date'}")
            divider()
            for i, r in enumerate(rows, 1):
                print(f"  {i:<3} {r['username']:<15} {r['category']:<20} "
                      f"{r['score']}/{r['total']:<5}  {r['percentage']:.1f}%   {r['played_on']}")
    except Error as e:
        print(f"  ❌ Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close(); conn.close()
    pause()


# ══════════════════════════════════════════════
#  MY HISTORY
# ══════════════════════════════════════════════

def show_my_history(user):
    banner()
    print(f"         📊  MY QUIZ HISTORY  ({user['username']})\n")
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.name AS category, s.score, s.total,
                   s.percentage,
                   DATE_FORMAT(s.played_at, '%d %b %Y %H:%i') AS played_on
            FROM scores s
            JOIN categories c ON s.category_id = c.id
            WHERE s.user_id = %s
            ORDER BY s.played_at DESC
        """, (user["id"],))
        rows = cursor.fetchall()
        if not rows:
            print("  You haven't played any quiz yet!")
        else:
            print(f"  {'#':<4} {'Category':<22} {'Score':<10} {'%':<10} {'Date'}")
            divider()
            for i, r in enumerate(rows, 1):
                print(f"  {i:<4} {r['category']:<22} {r['score']}/{r['total']:<8}  "
                      f"{r['percentage']:.1f}%   {r['played_on']}")
    except Error as e:
        print(f"  ❌ Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close(); conn.close()
    pause()


# ══════════════════════════════════════════════
#  MENUS
# ══════════════════════════════════════════════

def auth_menu():
    while True:
        banner()
        print("    [1]  Login")
        print("    [2]  Register")
        print("    [0]  Exit")
        divider()
        choice = input("  Your choice : ").strip()
        if choice == "1":
            user = login()
            if user: return user
        elif choice == "2":
            user = register()
            if user: return user
        elif choice == "0":
            print("\n  👋 Goodbye!\n")
            exit()
        else:
            print("  ❌ Invalid choice."); pause()


def main_menu(user):
    while True:
        banner()
        print(f"  👤  Logged in as: {user['username']}\n")
        print("    [1]  🎯  Start Quiz")
        print("    [2]  🏆  Leaderboard")
        print("    [3]  📊  My History")
        print("    [0]  🚪  Logout")
        divider()
        choice = input("  Your choice : ").strip()

        if choice == "1":
            category = choose_category()
            if category:
                conduct_quiz(user, category)
        elif choice == "2":
            show_leaderboard()
        elif choice == "3":
            show_my_history(user)
        elif choice == "0":
            print(f"\n  👋 Goodbye, {user['username']}!\n")
            break
        else:
            print("  ❌ Invalid choice."); pause()


# ══════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════

if __name__ == "__main__":
    try:
        while True:
            user = auth_menu()
            main_menu(user)
            banner()
            again = input("  Play again with another account? (y/n) : ").strip().lower()
            if again != "y":
                print("\n  👋 Thanks for playing! Goodbye!\n")
                break
    except KeyboardInterrupt:
        print("\n\n  👋 Exiting... Goodbye!\n")
