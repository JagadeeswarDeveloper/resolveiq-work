"""Illustrative business impact estimates; these are not production claims."""


def estimate_impact(
    complaints_per_day: float,
    average_handling_time_minutes: float,
    support_agent_cost_per_hour: float,
    automation_rate: float,
    average_resolution_time_hours: float,
) -> dict[str, float]:
    """Estimate hours, cost, and resolution-time reduction from automation."""
    daily_hours = complaints_per_day * average_handling_time_minutes / 60
    hours_saved = daily_hours * automation_rate
    cost_reduction = hours_saved * support_agent_cost_per_hour
    resolution_time_reduction = average_resolution_time_hours * automation_rate
    return {
        "estimated_hours_saved_per_day": round(hours_saved, 2),
        "estimated_support_cost_reduction_per_day": round(cost_reduction, 2),
        "estimated_resolution_time_reduction_hours": round(resolution_time_reduction, 2),
    }
