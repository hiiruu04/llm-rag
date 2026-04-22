from app.agents.mutation_service import (
    execute_analyzer_mutation,
    execute_scheduler_mutation,
)
from app.agents.router import get_agent_router
from app.mcp.server import mcp_server


@mcp_server.tool()
async def scheduling_agent(question: str, mutation: str | None = None) -> str:
    """Route a scheduling-related question to the Scheduling Agent.

    Handles queries about shifts, rosters, availability, assignments,
    workforce planning, and task scheduling.

    Args:
        question: Natural language question about scheduling
        mutation: Optional mutation command: 'assign_task:<task_uuid>:<worker_uuid>',
                  'update_task_status:<task_uuid>:<status>',
                  'reschedule_task:<task_uuid>:<shift_uuid>'
    """
    router = get_agent_router()
    response = await router.route(question, intent="scheduling")

    result = response.answer
    if response.data_used:
        result += f"\n\n[Data sources used: {', '.join(response.data_used)}]"

    if mutation:
        try:
            mutation_result = await execute_scheduler_mutation(mutation)
            result += f"\n\n[Scheduling mutation: {mutation_result}]"
        except Exception as e:
            result += f"\n\n[Scheduling mutation failed: {str(e)}]"

    return result


@mcp_server.tool()
async def competency_agent(question: str) -> str:
    """Route a competency-related question to the Competency Agent.

    Handles queries about worker skills, fitness-for-task clearance,
    training gaps, and proficiency assessments.

    Args:
        question: Natural language question about worker competency
    """
    router = get_agent_router()
    response = await router.route(question, intent="competency")
    result = response.answer
    if response.data_used:
        result += f"\n\n[Data sources used: {', '.join(response.data_used)}]"
    return result


@mcp_server.tool()
async def analyzer_agent(question: str, mutation: str | None = None) -> str:
    """Route an analysis-related question to the Analyzer Agent.

    Handles queries about MTTR, MTBF, KPIs, trends, statistics,
    performance metrics, and status overviews.

    Args:
        question: Natural language question about analysis or metrics
        mutation: Optional mutation command:
                  'log_down_event:<asset_uuid>:<fault_uuid>:<description>',
                  'close_down_event:<down_event_uuid>:<resolution>',
                  'update_fault_severity:<fault_uuid>:<severity>'
    """
    router = get_agent_router()
    response = await router.route(question, intent="analysis")

    result = response.answer
    if response.data_used:
        result += f"\n\n[Data sources used: {', '.join(response.data_used)}]"

    if mutation:
        try:
            mutation_result = await execute_analyzer_mutation(mutation)
            result += f"\n\n[Analysis mutation: {mutation_result}]"
        except Exception as e:
            result += f"\n\n[Analysis mutation failed: {str(e)}]"

    return result


@mcp_server.tool()
async def recommender_agent(question: str, mutation: str | None = None) -> str:
    """Route a recommendation-related question to the Recommender Agent.

    Handles queries about failures, anomalies, repairs, spare parts,
    troubleshooting, root cause analysis, and action documentation.

    Args:
        question: Natural language question about recommendations or troubleshooting
        mutation: Optional mutation command: 'close_action:<uuid>:<outcome>',
                  'record_outcome:<task_uuid>:<result>'
    """
    router = get_agent_router()
    response = await router.route(question, intent="recommendation")

    result = response.answer
    if response.data_used:
        result += f"\n\n[Data sources used: {', '.join(response.data_used)}]"

    if mutation:
        from app.agents.mutation_service import close_action, record_outcome

        try:
            parts = mutation.split(":", 2)
            action = parts[0]

            if action == "close_action" and len(parts) >= 3:
                outcome = parts[2] if len(parts) > 2 else "Completed"
                action_result = await close_action(parts[1], outcome)
                result += f"\n\n[Action closed: {action_result}]"
            elif action == "record_outcome" and len(parts) >= 3:
                outcome_text = parts[2]
                outcome_result = await record_outcome(parts[1], outcome_text)
                result += f"\n\n[Outcome recorded: {outcome_result}]"
            else:
                result += f"\n\n[Unknown mutation format: {mutation}]"
        except Exception as e:
            result += f"\n\n[Mutation failed: {str(e)}]"

    if response.sources:
        result += (
            "\n\n[Document sources: "
            + ", ".join(s.get("filename", "Unknown") for s in response.sources)
            + "]"
        )

    return result
