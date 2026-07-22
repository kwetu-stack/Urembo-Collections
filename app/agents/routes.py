from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request
)

from app.models.agent import Agent


agents_bp = Blueprint(
    "agents",
    __name__,
    url_prefix="/agents"
)


@agents_bp.route("/")
def agents():

    # ------------------------------------------------------
    # Login Protection
    # ------------------------------------------------------

    if not session.get("logged_in"):
        return redirect(
            url_for("auth.login")
        )


    # ------------------------------------------------------
    # Pagination Settings
    # ------------------------------------------------------

    page = request.args.get(
        "page",
        1,
        type=int
    )

    per_page = 100


    # ------------------------------------------------------
    # Query Agents
    # ------------------------------------------------------

    pagination = (
        Agent.query
        .order_by(Agent.agent_name)
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
    )


    agents = pagination.items


    # ------------------------------------------------------
    # Summary Statistics
    # ------------------------------------------------------

    total_agents = Agent.query.count()


    active_agents = (
        Agent.query
        .filter_by(status="Active")
        .count()
    )


    ama_agents = (
        Agent.query
        .filter_by(ama="YES")
        .count()
    )


    qama_agents = (
        Agent.query
        .filter_by(qama="YES")
        .count()
    )


    qdrso_agents = (
        Agent.query
        .filter_by(qdrso="YES")
        .count()
    )


    return render_template(
        "agents/agents.html",
        agents=agents,
        pagination=pagination,
        total_agents=total_agents,
        active_agents=active_agents,
        ama_agents=ama_agents,
        qama_agents=qama_agents,
        qdrso_agents=qdrso_agents,
    )