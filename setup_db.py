import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Sambit@123",  # ← Change this
}

DB_NAME = "quiz_app_db"


def create_database(cursor):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")
    print(f"✅ Database '{DB_NAME}' ready.")


def create_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_id INT,
            question TEXT NOT NULL,
            option_a VARCHAR(255) NOT NULL,
            option_b VARCHAR(255) NOT NULL,
            option_c VARCHAR(255) NOT NULL,
            option_d VARCHAR(255) NOT NULL,
            correct_option CHAR(1) NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            category_id INT,
            score INT NOT NULL,
            total INT NOT NULL,
            percentage FLOAT NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    print("✅ Tables created.")


def insert_sample_data(cursor):
    categories = ["Python", "General Knowledge", "Mathematics"]
    for cat in categories:
        cursor.execute("INSERT IGNORE INTO categories (name) VALUES (%s)", (cat,))

    cursor.execute("SELECT id, name FROM categories")
    cat_map = {name: cid for cid, name in cursor.fetchall()}

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

    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany("""
            INSERT INTO questions (category_id, question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, questions)
        print(f"✅ {len(questions)} sample questions inserted.")
    else:
        print(f"ℹ️  Questions already exist ({count} found). Skipping insert.")


def setup():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        create_database(cursor)
        create_tables(cursor)
        insert_sample_data(cursor)
        conn.commit()
        print("\n🎉 Database setup complete! You can now run: python quiz_app.py")
    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    setup()
