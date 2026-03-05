from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardTriageResponse, RecentActivityRead, TriageClientRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/triage", response_model=DashboardTriageResponse)
def get_trainer_triage(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    triage_rows = db.execute(
        text(
            """
            WITH assigned_clients AS (
                SELECT c.id AS client_id, c.name AS client_name
                FROM clients c
                WHERE c.trainer_id = :trainer_id
            ),
            ranked_logs AS (
                SELECT
                    wl.client_id,
                    wl.status,
                    ROW_NUMBER() OVER (
                        PARTITION BY wl.client_id
                        ORDER BY wl.logged_date DESC, wl.created_at DESC
                    ) AS rn
                FROM workout_logs wl
                JOIN assigned_clients ac ON ac.client_id = wl.client_id
            ),
            missed_last_two AS (
                SELECT
                    rl.client_id,
                    COALESCE(SUM(CASE WHEN rl.rn <= 2 AND rl.status = 'missed' THEN 1 ELSE 0 END), 0) AS missed_last_two
                FROM ranked_logs rl
                GROUP BY rl.client_id
            ),
            avg_rpe AS (
                SELECT
                    wl.client_id,
                    AVG(sl.actual_rpe) AS avg_rpe_last_14d
                FROM workout_logs wl
                JOIN set_logs sl ON sl.workout_log_id = wl.id
                JOIN assigned_clients ac ON ac.client_id = wl.client_id
                WHERE wl.logged_date >= (CURRENT_DATE - INTERVAL '14 days')
                GROUP BY wl.client_id
            ),
            latest_checkin AS (
                SELECT
                    dc.client_id,
                    MAX(dc.check_in_date) AS last_check_in_date
                FROM daily_checkins dc
                JOIN assigned_clients ac ON ac.client_id = dc.client_id
                GROUP BY dc.client_id
            ),
            latest_completed AS (
                SELECT
                    wl.client_id,
                    MAX(wl.completed_at) AS last_workout_completed_at
                FROM workout_logs wl
                JOIN assigned_clients ac ON ac.client_id = wl.client_id
                WHERE wl.status = 'completed'
                GROUP BY wl.client_id
            )
            SELECT
                ac.client_id,
                ac.client_name,
                COALESCE(mlt.missed_last_two, 0) AS missed_last_two,
                ar.avg_rpe_last_14d,
                lc.last_check_in_date,
                lcomp.last_workout_completed_at
            FROM assigned_clients ac
            LEFT JOIN missed_last_two mlt ON mlt.client_id = ac.client_id
            LEFT JOIN avg_rpe ar ON ar.client_id = ac.client_id
            LEFT JOIN latest_checkin lc ON lc.client_id = ac.client_id
            LEFT JOIN latest_completed lcomp ON lcomp.client_id = ac.client_id
            ORDER BY ac.client_name ASC
            """
        ),
        {"trainer_id": current_user.id},
    ).mappings().all()

    today = date.today()
    clients: list[TriageClientRead] = []

    for row in triage_rows:
        missed_last_two = int(row["missed_last_two"] or 0)
        avg_rpe = float(row["avg_rpe_last_14d"]) if row["avg_rpe_last_14d"] is not None else None
        last_check_in_date = row["last_check_in_date"]

        if missed_last_two >= 2 or (avg_rpe is not None and avg_rpe > 9):
            status = "red"
        elif missed_last_two == 1 or last_check_in_date != today:
            status = "yellow"
        else:
            status = "green"

        clients.append(
            TriageClientRead(
                client_id=str(row["client_id"]),
                client_name=row["client_name"] or "Unnamed Client",
                status=status,
                missed_last_two=missed_last_two,
                avg_rpe_last_14d=avg_rpe,
                last_check_in_date=last_check_in_date,
                last_workout_completed_at=row["last_workout_completed_at"],
            )
        )

    activity_rows = db.execute(
        text(
            """
            SELECT
                wl.id AS workout_log_id,
                wl.client_id,
                c.name AS client_name,
                wl.logged_date,
                wl.completed_at,
                wl.status
            FROM workout_logs wl
            JOIN clients c ON c.id = wl.client_id
            WHERE c.trainer_id = :trainer_id
              AND wl.status = 'completed'
            ORDER BY wl.completed_at DESC NULLS LAST, wl.logged_date DESC
            LIMIT 25
            """
        ),
        {"trainer_id": current_user.id},
    ).mappings().all()

    recent_activity = [
        RecentActivityRead(
            workout_log_id=str(row["workout_log_id"]),
            client_id=str(row["client_id"]),
            client_name=row["client_name"] or "Unnamed Client",
            logged_date=row["logged_date"],
            completed_at=row["completed_at"],
            status=row["status"],
        )
        for row in activity_rows
    ]

    return DashboardTriageResponse(clients=clients, recent_activity=recent_activity)
