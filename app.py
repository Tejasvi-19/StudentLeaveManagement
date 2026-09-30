from flask import Flask, render_template, request, redirect, session
from database import create_tables, get_db_connection

app = Flask(__name__)

app.secret_key = "student_leave_secret_key"

create_tables()


# Home page
@app.route("/")
def home():
    return redirect("/login")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")

            return redirect("/student")

        else:
            return render_template(
                "login.html",
                message="Invalid username or password"
            )

    return render_template("login.html")


# Student Registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()

        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            conn.close()

            return render_template(
                "register.html",
                message="Username already exists"
            )

        conn.execute(
            """
            INSERT INTO users (name, username, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (name, username, password, "student")
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# Student page
@app.route("/student")
@app.route("/student")
def student():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "student_dashboard.html",
        name=user["name"]
    )

# Admin page
@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/student")

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    leaves = conn.execute(
        """
        SELECT
            leaves.id,
            leaves.from_date,
            leaves.to_date,
            leaves.reason,
            leaves.status,
            users.name AS student_name
        FROM leaves
        JOIN users ON leaves.student_id = users.id
        ORDER BY leaves.id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        name=user["name"],
        leaves=leaves
    )


@app.route("/apply-leave", methods=["GET", "POST"])
def apply_leave():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "student":
        return redirect("/login")

    if request.method == "POST":

        from_date = request.form["from_date"]
        to_date = request.form["to_date"]
        reason = request.form["reason"]

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO leaves
            (student_id, from_date, to_date, reason, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                from_date,
                to_date,
                reason,
                "Pending"
            )
        )

        conn.commit()
        conn.close()

        return redirect("/my-leaves")

    return render_template("apply_leave.html")
@app.route("/my-leaves")
def my_leaves():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "student":
        return redirect("/login")

    conn = get_db_connection()

    leaves = conn.execute(
        """
        SELECT * FROM leaves
        WHERE student_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "my_leaves.html",
        leaves=leaves
    )

@app.route("/update-leave/<int:leave_id>", methods=["POST"])
def update_leave(leave_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/student")

    status = request.form["status"]

    if status not in ["Approved", "Rejected"]:
        return redirect("/admin")

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE leaves
        SET status = ?
        WHERE id = ?
        """,
        (status, leave_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

