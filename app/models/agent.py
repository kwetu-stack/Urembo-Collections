from app import db


class Agent(db.Model):
    __tablename__ = "agents"

    id = db.Column(db.Integer, primary_key=True)

    agent_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    agent_name = db.Column(
        db.String(150),
        nullable=False,
    )

    site = db.Column(db.String(150))

    tse = db.Column(db.String(150))

    ama = db.Column(db.String(20))

    qama = db.Column(db.String(20))

    qdrso = db.Column(db.String(20))

    status = db.Column(db.String(30))

    def __repr__(self):
        return f"<Agent {self.agent_name}>"