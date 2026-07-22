from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)


auth_bp = Blueprint("auth", __name__)


USERNAME = "joyce"
PASSWORD = "joyce123"


@auth_bp.route("/")
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:

            session["logged_in"] = True
            session["username"] = username

            return redirect(
                url_for("dashboard.dashboard")
            )

        return render_template(
            "auth/login.html",
            error="Invalid username or password"
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.login")
    )