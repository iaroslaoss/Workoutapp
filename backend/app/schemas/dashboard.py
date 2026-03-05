from datetime import date, datetime

from pydantic import BaseModel


class TriageClientRead(BaseModel):
    client_id: str
    client_name: str
    status: str
    missed_last_two: int
    avg_rpe_last_14d: float | None
    last_check_in_date: date | None
    last_workout_completed_at: datetime | None


class RecentActivityRead(BaseModel):
    workout_log_id: str
    client_id: str
    client_name: str
    logged_date: date
    completed_at: datetime | None
    status: str


class DashboardTriageResponse(BaseModel):
    clients: list[TriageClientRead]
    recent_activity: list[RecentActivityRead]
