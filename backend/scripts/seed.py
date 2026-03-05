from sqlalchemy import select

from app.core.security import get_password_hash
import app.db.base  # noqa: F401
from app.db.session import SessionLocal
from app.models.exercise import Exercise
from app.models.user import User

GLOBAL_EXERCISES = [
    ("Barbell Back Squat", "legs", "Barbell", "Quads", "3-1-1-0", "Foundational lower body strength movement."),
    ("Romanian Deadlift", "pull", "Barbell", "Hamstrings", "3-1-1-0", "Hip hinge focused on posterior chain."),
    ("Barbell Bench Press", "push", "Barbell", "Chest", "3-1-1-0", "Classic horizontal press."),
    ("Incline Dumbbell Press", "push", "Dumbbells", "Upper Chest", "3-1-1-0", "Upper chest pressing pattern."),
    ("Pull-Up", "pull", "Bodyweight", "Lats", "2-1-1-1", "Vertical pulling movement."),
    ("Seated Cable Row", "pull", "Cable", "Mid Back", "2-1-2-0", "Horizontal rowing pattern."),
    ("Overhead Press", "push", "Barbell", "Shoulders", "2-1-1-0", "Vertical press for shoulder strength."),
    ("Walking Lunge", "legs", "Dumbbells", "Quads", "2-0-1-0", "Unilateral lower body work."),
    ("Leg Press", "legs", "Machine", "Quads", "2-0-2-0", "Machine quad-dominant press."),
    ("Hamstring Curl", "legs", "Machine", "Hamstrings", "2-1-2-0", "Knee flexion isolation."),
    ("Plank", "core", "Bodyweight", "Core", "0-30-0-0", "Isometric anti-extension core hold."),
    ("Dead Bug", "core", "Bodyweight", "Core", "2-1-2-1", "Core control and breathing pattern."),
    ("Face Pull", "pull", "Cable", "Rear Delts", "2-1-2-0", "Scapular retraction and shoulder health."),
    ("Air Bike Intervals", "cardio", "Bike", "Conditioning", "0-0-0-0", "High-intensity cardio intervals."),
    ("Farmer Carry", "other", "Dumbbells", "Grip", "0-0-0-0", "Loaded carry for grip and core stability."),
]


def main() -> None:
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@liftmove.local"))
        if not admin:
            admin = User(email="admin@liftmove.local", password_hash=get_password_hash("Admin123!"), role="admin")
            db.add(admin)
            db.flush()

        existing = {name for (name,) in db.execute(select(Exercise.name)).all()}
        for name, category, equipment, muscle_group, default_tempo, description in GLOBAL_EXERCISES:
            if name in existing:
                continue
            db.add(
                Exercise(
                    name=name,
                    category=category,
                    equipment=equipment,
                    muscle_group=muscle_group,
                    default_tempo=default_tempo,
                    description=description,
                    created_by_trainer_id=None,
                )
            )

        db.commit()
        print("Seed complete. Admin user: admin@liftmove.local / Admin123!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
