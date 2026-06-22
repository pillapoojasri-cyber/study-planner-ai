from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from groq import Groq

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
from datetime import date, timedelta
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password == confirm_password:

            conn = sqlite3.connect("tasks.db")
            cursor = conn.cursor()

            # Check email
            cursor.execute("""
            SELECT * FROM users
            WHERE email = ?
            """, (email,))

            existing_email = cursor.fetchone()

            if existing_email:
                conn.close()
                return render_template(
                    "signup.html",
                    error="Email already registered"
                )

            # Check username
            cursor.execute("""
            SELECT * FROM users
            WHERE username = ?
            """, (username,))

            existing_username = cursor.fetchone()

            if existing_username:
                conn.close()
                return render_template(
                    "signup.html",
                    error="Username already exists"
                )

            cursor.execute("""
            INSERT INTO users(fullname, email, username, password)
            VALUES(?, ?, ?, ?)
            """, (fullname, email, username, password))

            conn.commit()
            conn.close()

            return redirect("/login")

        else:
            return render_template(
                "signup.html",
                error="Passwords do not match"
            )

    return render_template("signup.html")
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        print("Username:", username)
        print("Password:", password)

        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM users
        WHERE username = ? AND password = ?
        """, (username, password))

        user = cursor.fetchone()

        print("User found:", user)

        conn.close()

        if user:
             session["username"] = username
             return redirect("/home")
        else:
            return render_template(
    "login.html",
    error="Invalid Username or Password!"
)
    return render_template("login.html")
@app.route("/logout")
def logout():

    session.pop("username", None)

    return redirect("/login")
@app.route("/home", methods=["GET", "POST"])
def home():
    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        task = request.form["task"]
        due_date = request.form["due_date"]
        due_time = request.form["due_time"]

        if task.strip() != "":

            conn = sqlite3.connect("tasks.db")
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO tasks(task, due_date, due_time,username)
            VALUES(?, ?, ?,?)
            """, (task, due_date, due_time,session["username"]))

            conn.commit()
            conn.close()

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("""
SELECT * FROM tasks
WHERE username = ?
""", (session["username"],))

    tasks = cursor.fetchall()

    conn.close()

    total_tasks = len(tasks)

    completed_tasks = 0

    for task in tasks:
        if task[2] == 1:
            completed_tasks += 1

    pending_tasks = total_tasks - completed_tasks
    cursor = sqlite3.connect("tasks.db").cursor()
    cursor.execute("""
SELECT streak
FROM streaks
WHERE username = ?
""", (session["username"],))
    row = cursor.fetchone()
    current_streak = row[0] if row else 0

    return render_template(
    "index.html",
    tasks=tasks,
    total_tasks=total_tasks,
    completed_tasks=completed_tasks,
    pending_tasks=pending_tasks,
    current_streak=current_streak
)


@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM tasks
    WHERE id = ? AND username=?
    """, (id,session["username"]))

    conn.commit()
    conn.close()

    return redirect("/home")
@app.route("/complete/<int:id>")
def complete(id):

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE tasks
    SET completed = 1
    WHERE id = ? AND username = ?
    """, (id, session["username"]))

    conn.commit()

    today = str(date.today())

    cursor.execute("""
    SELECT streak, last_completed_date
    FROM streaks
    WHERE username = ?
    """, (session["username"],))

    result = cursor.fetchone()

    if result:

        streak = result[0]
        last_date = result[1]

        if last_date == str(date.today() - timedelta(days=1)):
            streak += 1

        elif last_date != today:
            streak = 1

        cursor.execute("""
        UPDATE streaks
        SET streak = ?, last_completed_date = ?
        WHERE username = ?
        """, (streak, today, session["username"]))

    else:

        cursor.execute("""
        INSERT INTO streaks(username, streak, last_completed_date)
        VALUES(?, ?, ?)
        """, (session["username"], 1, today))

    conn.commit()
    conn.close()

    return redirect("/home")
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    if request.method == "POST":

        new_task = request.form["task"]
        due_date = request.form["due_date"]
        due_time = request.form["due_time"]

        cursor.execute("""
        UPDATE tasks
        SET task = ?, due_date = ?, due_time = ?
        WHERE id = ? AND username=?
        """, (new_task, due_date, due_time, id,session["username"]))

        conn.commit()
        conn.close()

        return redirect("/home")

    cursor.execute("""
    SELECT * FROM tasks
    WHERE id = ? AND username=?
    """, (id,session["username"]))

    task = cursor.fetchone()

    conn.close()

    return render_template(
        "edit.html",
        task=task
    )
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return render_template(
                "forgot_password.html",
                error="Passwords do not match"
            )

        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET password = ?
            WHERE username = ? AND email = ?
        """, (new_password, username, email))

        if cursor.rowcount == 0:
            conn.close()
            return render_template(
                "forgot_password.html",
                error="Username and Email do not match"
            )

        conn.commit()
        conn.close()
        return render_template(
            "forgot_password.html",
            success="Password updated successfully. You can now log in."
        )

    return render_template("forgot_password.html")

@app.route("/study_help/<int:id>")
def study_help(id):

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT task
    FROM tasks
    WHERE id = ?
    """, (id,))

    task = cursor.fetchone()

    conn.close()

    topic = task[0]

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""
You are an expert study coach.

Topic: {topic}

Generate a detailed study guide containing:

📚 Topic Overview

🎯 Learning Objectives

📝 Important Concepts

🛣 Step-by-Step Learning Path

❓ 5 Practice Questions

⚠ Common Mistakes to Avoid

⏱ 30-Minute Study Plan

💡 Quick Revision Notes

Explain everything in a beginner-friendly way using headings and bullet points.
"""
            }
        ],
        model="llama-3.3-70b-versatile"
    )

    guide = response.choices[0].message.content

    return render_template(
        "study_help.html",
        topic=topic,
        guide=guide
    )
if __name__ == "__main__":
    app.run(debug=True)