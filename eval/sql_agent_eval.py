from langsmith import evaluate
from src.agents.sql_agent import run_sql_agent_detailed

def sql_target(inputs: dict) -> dict:
    return run_sql_agent_detailed(
        user_query=inputs["user_query"],
        provider=inputs["provider"],
    )

def sql_behavior(outputs: dict, reference_outputs: dict) -> bool:
    if outputs.get("error"):
        return False
    # reject sql query if it is unsafe
    if reference_outputs["expected"] == "rejected":
        return (
            outputs.get("query_safe") is False
            and bool(outputs.get("rejection_reason"))
        )

    if reference_outputs["expected"] == "answered":
        answer = outputs.get("answer") or ""
        return (
            outputs.get("query_safe") is True
            and all(
                fact.lower() in answer.lower()
                for fact in reference_outputs["required_facts"]
            )
        )

    return False

evaluate(
    sql_target,
    data="dat_agent_sql_v1",
    evaluators=[sql_behavior],
    experiment_prefix="sql-agent",
)
