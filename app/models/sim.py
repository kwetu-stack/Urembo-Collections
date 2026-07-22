from app import db


class SimIssuance(db.Model):

    __tablename__ = "sim_issuance"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    dso_id = db.Column(
        db.String(50)
    )

    sim_serial = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    distributor_name = db.Column(
        db.String(150)
    )

    order_date = db.Column(
        db.String(50)
    )

    email = db.Column(
        db.String(150)
    )

    order_reference = db.Column(
        db.String(100)
    )

    kyc_msisdn = db.Column(
        db.String(50)
    )

    served_msisdn = db.Column(
        db.String(50)
    )

    kyc_created_on = db.Column(
        db.String(50)
    )

    activation_time = db.Column(
        db.String(50)
    )

    device_technology = db.Column(
        db.String(50)
    )

    recharge_amount = db.Column(
        db.Float
    )

    retailer_msisdn = db.Column(
        db.String(50)
    )

    promoter_msisdn = db.Column(
        db.String(50)
    )

    zone_name = db.Column(
        db.String(50)
    )


    def __repr__(self):
        return f"<SIM {self.sim_serial}>"