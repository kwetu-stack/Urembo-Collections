from datetime import date
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models.performance import PerformanceSnapshot


app = create_app()


with app.app_context():

    print("=" * 60)
    print("PERFORMANCE SNAPSHOT SEED")
    print("=" * 60)

    existing = PerformanceSnapshot.query.filter_by(
        report_date=date(2026, 7, 16)
    ).first()

    if existing:
        print("Performance report already exists.")
        sys.exit()

    performance = PerformanceSnapshot(

        report_date=date(2026, 7, 16),

        partner_name="MIKINDANI UREMBO COLLECTIONS",

        contract_status="PARTIAL DOCUMENTS SHARED",

        gross_adds=583,
        gross_adds_target=2000,

        sim_billing=1250,
        sim_billing_target=2000,

        active_agents_percent=81,
        active_agents_target=100,

        back_margin_rate=1.75,
        target_back_margin_rate=3.75,

        primaries_purchased=95000,

        agent_led_airtime=20254,

        retailer_self_recharges=88360,

        total_airtime=203614,

        projected_commission=3563,

        total_agents=75,

        active_agents=61,
    )


    db.session.add(performance)

    db.session.commit()


    print("\nPerformance snapshot created successfully.")
    print("-" * 60)

    print("Report Date :", performance.report_date)
    print("Partner     :", performance.partner_name)
    print("Gross Adds  :", performance.gross_adds)
    print("SIM Billing :", performance.sim_billing)
    print("Back Margin :", performance.back_margin_rate, "%")
    print("Commission  :", performance.projected_commission)

    print("=" * 60)