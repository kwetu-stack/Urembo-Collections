from app import db


class PerformanceSnapshot(db.Model):

    __tablename__ = "performance_snapshots"

    id = db.Column(db.Integer, primary_key=True)

    report_date = db.Column(db.Date, nullable=False)

    partner_name = db.Column(db.String(150), nullable=False)

    contract_status = db.Column(db.String(100))

    gross_adds = db.Column(db.Integer)
    gross_adds_target = db.Column(db.Integer, default=2000)

    sim_billing = db.Column(db.Integer)
    sim_billing_target = db.Column(db.Integer, default=2000)

    active_agents_percent = db.Column(db.Float)
    active_agents_target = db.Column(db.Float, default=100.0)

    back_margin_rate = db.Column(db.Float)
    target_back_margin_rate = db.Column(db.Float, default=3.75)

    primaries_purchased = db.Column(db.Float)

    agent_led_airtime = db.Column(db.Float)

    retailer_self_recharges = db.Column(db.Float)

    total_airtime = db.Column(db.Float)

    projected_commission = db.Column(db.Float)

    total_agents = db.Column(db.Integer)

    active_agents = db.Column(db.Integer)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def __repr__(self):
        return f"<PerformanceSnapshot {self.report_date}>"