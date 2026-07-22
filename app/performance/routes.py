from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from app.models.performance import PerformanceSnapshot


performance_bp = Blueprint(
    "performance",
    __name__,
    url_prefix="/performance"
)


@performance_bp.route("/")
def performance():

    # ------------------------------------------------------
    # Login Protection
    # ------------------------------------------------------

    if not session.get("logged_in"):
        return redirect(
            url_for("auth.login")
        )


    # ------------------------------------------------------
    # Latest Performance Report
    # ------------------------------------------------------

    report = (
        PerformanceSnapshot.query
        .order_by(
            PerformanceSnapshot.report_date.desc()
        )
        .first()
    )


    return render_template(
        "performance/performance.html",
        report=report
    )