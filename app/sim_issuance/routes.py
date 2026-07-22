from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for
)

from sqlalchemy import func

from app import db
from app.models.sim import SimIssuance


sim_bp = Blueprint(
    "sim",
    __name__,
    url_prefix="/sim-issuance"
)


@sim_bp.route("/")
def sim_issuance():

    # ------------------------------------------------------
    # Login Protection
    # ------------------------------------------------------

    if not session.get("logged_in"):
        return redirect(
            url_for("auth.login")
        )


    # ------------------------------------------------------
    # Pagination
    # ------------------------------------------------------

    page = request.args.get(
        "page",
        1,
        type=int
    )

    per_page = 100


    pagination = (
        SimIssuance.query
        .order_by(
            SimIssuance.activation_time.desc()
        )
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
    )


    sims = pagination.items


    # ------------------------------------------------------
    # Summary Statistics
    # ------------------------------------------------------

    total_sims = (
        SimIssuance.query.count()
    )


    activated_sims = (
        SimIssuance.query
        .filter(
            SimIssuance.activation_time.isnot(None)
        )
        .count()
    )


    retailers = (
        db.session.query(
            func.count(
                func.distinct(
                    SimIssuance.retailer_msisdn
                )
            )
        )
        .scalar()
    )


    total_recharge = (
        db.session.query(
            func.sum(
                SimIssuance.recharge_amount
            )
        )
        .scalar()
    ) or 0



    return render_template(
        "sim_issuance/sim_issuance.html",

        sims=sims,

        pagination=pagination,

        total_sims=total_sims,

        activated_sims=activated_sims,

        retailers=retailers,

        total_recharge=total_recharge,
    )