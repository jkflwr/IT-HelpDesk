from flask import Flask, redirect, render_template, request, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = sqlite3.connect("helpdesk.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user[3], password):

            session["username"] = username
            session["role"] = user[4]

            return redirect("/dashboard")

        else:

            return render_template(
                "login.html",
                error="Invalid username or password."
            )

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        connection = sqlite3.connect("helpdesk.db")
        cursor = connection.cursor()

        try:

            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )

            connection.commit()

            session["username"] = username

            connection.close()

            return redirect("/dashboard")

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error="Username or email already exists."
            )

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    return render_template("dashboard.html", username=session["username"])

@app.route("/tickets")
def tickets():
    if "username" not in session:
        return redirect("/login")
    connection = sqlite3.connect("helpdesk.db")
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT tickets.*
        FROM tickets
        JOIN users ON tickets.user_id = users.id
        WHERE users.username = ?
        """,
        (session["username"],)
    )

    tickets = cursor.fetchall()

    connection.close()

    return render_template("tickets.html", tickets=tickets)

@app.route("/ticket", methods=["GET", "POST"])
def ticket():
    if "username" not in session:
        return redirect("/login")
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]  
        connection = sqlite3.connect("helpdesk.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (session["username"],)
        )

        user = cursor.fetchone()

        cursor.execute(
            "INSERT INTO tickets (title, description, status, user_id) VALUES (?, ?, ?, ?)",
            (title, description, "Open", user[0])
        )

        connection.commit()
        connection.close()

        return redirect("/tickets")
    return render_template("ticket.html")

@app.route("/support")
def support():
    return render_template("support.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/support/tickets")
def support_tickets():

    if "username" not in session:
        return redirect("/login")

    if session["role"] != "support":
        return redirect("/dashboard")

    connection = sqlite3.connect("helpdesk.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT tickets.*, users.username
        FROM tickets
        JOIN users ON tickets.user_id = users.id
    """)

    tickets = cursor.fetchall()

    connection.close()

    return render_template("support_tickets.html", tickets=tickets)

@app.route("/update_status", methods=["POST"])
def update_status():

    if "username" not in session:
        return redirect("/login")

    if session["role"] != "support":
        return redirect("/dashboard")

    ticket_id = request.form["ticket_id"]
    status = request.form["status"]

    connection = sqlite3.connect("helpdesk.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE tickets SET status = ? WHERE id = ?",
        (status, ticket_id)
    )

    connection.commit()
    connection.close()

    return redirect("/support/tickets")


@app.route("/send_message", methods=["POST"])
def send_message():

    if "username" not in session:
        return redirect("/login")

    if session["role"] != "support":
        return redirect("/dashboard")

    ticket_id = request.form["ticket_id"]
    message = request.form["message"]

    connection = sqlite3.connect("helpdesk.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE tickets SET support_message = ? WHERE id = ?",
        (message, ticket_id)
    )

    connection.commit()
    connection.close()

    return redirect("/support/tickets")


if __name__ == "__main__":
    app.run(debug=True)