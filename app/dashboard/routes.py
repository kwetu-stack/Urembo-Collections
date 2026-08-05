from flask import Blueprint, render_template, session, redirect, url_for

from app.models.agent import Agent
from app.models.sim import SimIssuance
from app.models.performance import PerformanceSnapshot

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
def dashboard():

    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))

    # Existing dashboard code continues here...

    # --------------------------------------------------
    # Operational Metrics
    # --------------------------------------------------

    total_agents = Agent.query.count()

    total_sims = SimIssuance.query.count()

    activated_sims = SimIssuance.query.filter(
        SimIssuance.activation_time.isnot(None)
    ).count()

    retailers = (
        SimIssuance.query.with_entities(SimIssuance.retailer_msisdn).distinct().count()
    )

    # --------------------------------------------------
    # Latest Performance Snapshot
    # --------------------------------------------------

    report = PerformanceSnapshot.query.order_by(
        PerformanceSnapshot.report_date.desc()
    ).first()
    if report:
        gross_adds = report.gross_adds or 0
        gross_target = report.gross_adds_target or 0

        sim_billing = report.sim_billing or 0
        sim_target = report.sim_billing_target or 0

        active_percent = report.active_agents_percent or 0
        active_target = report.active_agents_target or 0

        gross_adds_gap = max(gross_target - gross_adds, 0)

        sim_billing_gap = max(sim_target - sim_billing, 0)

        active_agents_gap = max(active_target - active_percent, 0)
    else:
        gross_adds_gap = 0
        sim_billing_gap = 0
        active_agents_gap = 0

    return render_template(
        "dashboard/dashboard.html",
        total_agents=total_agents,
        total_sims=total_sims,
        activated_sims=activated_sims,
        retailers=retailers,
        report=report,
        gross_adds_gap=gross_adds_gap,
        sim_billing_gap=sim_billing_gap,
        active_agents_gap=active_agents_gap,
    )
