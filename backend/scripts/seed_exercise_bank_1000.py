from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import func, select

import app.db.base  # noqa: F401
from app.db.session import SessionLocal
from app.models.exercise import Exercise

TARGET_NEW_EXERCISES = 1000
TARGET_TOTAL_EXERCISES = 1015

CATEGORY_TEMPO = {
    "push": "3-1-1-0",
    "pull": "3-1-1-0",
    "legs": "3-1-1-0",
    "core": "2-1-2-1",
    "cardio": "0-0-0-0",
    "other": "2-0-2-0",
}

EQUIPMENT_SCORE = {
    "Bodyweight": 26,
    "Dumbbells": 24,
    "Barbell": 22,
    "Kettlebell": 21,
    "Cable": 19,
    "Machine": 17,
    "Band": 16,
    "Landmine": 14,
    "EZ Bar": 14,
    "Smith Machine": 13,
    "Trap Bar": 13,
    "Suspension Trainer": 12,
    "Medicine Ball": 11,
    "Sled": 10,
    "Bike": 9,
    "Rower": 9,
    "Elliptical": 8,
    "Stairs": 8,
    "Sandbag": 8,
    "Battle Rope": 8,
    "Treadmill": 8,
}

VARIATION_SCORE = {
    "Standard": 30,
    "Paused": 24,
    "Tempo": 23,
    "Controlled": 22,
    "Alternating": 21,
    "Single-Arm": 20,
    "Single-Leg": 20,
    "Seated": 19,
    "Standing": 19,
    "Incline": 18,
    "Decline": 17,
    "Wide-Stance": 16,
    "Narrow-Stance": 16,
    "Deficit": 15,
    "Isometric": 14,
    "Explosive": 14,
    "Reverse": 13,
}


@dataclass(frozen=True)
class Candidate:
    name: str
    category: str
    equipment: str
    muscle_group: str
    default_tempo: str
    description: str
    score: int


@dataclass(frozen=True)
class Family:
    base: str
    category: str
    muscle_group: str
    equipments: tuple[str, ...]
    variations: tuple[str, ...]
    base_score: int


CURATED_CORE = [
    ("Barbell Back Squat", "legs", "Barbell", "Quads"),
    ("Barbell Front Squat", "legs", "Barbell", "Quads"),
    ("Romanian Deadlift", "pull", "Barbell", "Hamstrings"),
    ("Conventional Deadlift", "pull", "Barbell", "Posterior Chain"),
    ("Trap Bar Deadlift", "pull", "Trap Bar", "Posterior Chain"),
    ("Barbell Bench Press", "push", "Barbell", "Chest"),
    ("Incline Dumbbell Press", "push", "Dumbbells", "Upper Chest"),
    ("Overhead Press", "push", "Barbell", "Shoulders"),
    ("Push-Up", "push", "Bodyweight", "Chest"),
    ("Weighted Pull-Up", "pull", "Bodyweight", "Lats"),
    ("Chin-Up", "pull", "Bodyweight", "Lats"),
    ("Seated Cable Row", "pull", "Cable", "Mid Back"),
    ("Single-Arm Dumbbell Row", "pull", "Dumbbells", "Lats"),
    ("Walking Lunge", "legs", "Dumbbells", "Quads"),
    ("Bulgarian Split Squat", "legs", "Dumbbells", "Quads"),
    ("Leg Press", "legs", "Machine", "Quads"),
    ("Leg Curl", "legs", "Machine", "Hamstrings"),
    ("Hip Thrust", "legs", "Barbell", "Glutes"),
    ("Calf Raise", "legs", "Machine", "Calves"),
    ("Plank", "core", "Bodyweight", "Core"),
    ("Side Plank", "core", "Bodyweight", "Core"),
    ("Dead Bug", "core", "Bodyweight", "Core"),
    ("Pallof Press", "core", "Cable", "Core"),
    ("Hanging Knee Raise", "core", "Bodyweight", "Abs"),
    ("Ab Wheel Rollout", "core", "Bodyweight", "Abs"),
    ("Farmer Carry", "other", "Dumbbells", "Grip"),
    ("Suitcase Carry", "other", "Dumbbells", "Core"),
    ("Turkish Get-Up", "other", "Kettlebell", "Full Body"),
    ("Battle Rope Slams", "other", "Battle Rope", "Conditioning"),
    ("Air Bike Intervals", "cardio", "Bike", "Conditioning"),
    ("Rower Intervals", "cardio", "Rower", "Conditioning"),
    ("Treadmill Intervals", "cardio", "Treadmill", "Conditioning"),
    ("Stair Climb", "cardio", "Stairs", "Conditioning"),
    ("Sled Push", "other", "Sled", "Conditioning"),
    ("Sled Drag", "other", "Sled", "Conditioning"),
]


FAMILIES: tuple[Family, ...] = (
    Family("Bench Press", "push", "Chest", ("Barbell", "Dumbbells", "Smith Machine", "Machine"), ("Standard", "Paused", "Tempo", "Incline", "Decline", "Controlled"), 82),
    Family("Shoulder Press", "push", "Shoulders", ("Barbell", "Dumbbells", "Machine", "Kettlebell"), ("Standard", "Seated", "Standing", "Single-Arm", "Tempo"), 78),
    Family("Overhead Press", "push", "Shoulders", ("Barbell", "Dumbbells", "Kettlebell"), ("Standard", "Paused", "Tempo", "Single-Arm", "Standing"), 76),
    Family("Push-Up", "push", "Chest", ("Bodyweight", "Band", "Suspension Trainer"), ("Standard", "Tempo", "Paused", "Decline", "Incline", "Explosive"), 74),
    Family("Dip", "push", "Triceps", ("Bodyweight", "Band", "Machine"), ("Standard", "Tempo", "Paused", "Controlled"), 72),
    Family("Chest Fly", "push", "Chest", ("Dumbbells", "Cable", "Machine", "Band"), ("Standard", "Incline", "Decline", "Standing", "Controlled"), 67),
    Family("Lateral Raise", "push", "Shoulders", ("Dumbbells", "Cable", "Band", "Machine"), ("Standard", "Seated", "Standing", "Single-Arm", "Paused"), 64),
    Family("Front Raise", "push", "Shoulders", ("Dumbbells", "Cable", "Band", "EZ Bar"), ("Standard", "Alternating", "Single-Arm", "Controlled"), 60),
    Family("Triceps Extension", "push", "Triceps", ("Dumbbells", "Cable", "EZ Bar", "Band"), ("Standard", "Overhead", "Seated", "Single-Arm", "Controlled"), 63),
    Family("Triceps Pressdown", "push", "Triceps", ("Cable", "Band"), ("Standard", "Single-Arm", "Reverse", "Paused"), 62),
    Family("Landmine Press", "push", "Shoulders", ("Landmine",), ("Standard", "Single-Arm", "Standing", "Alternating", "Tempo"), 66),
    Family("Arnold Press", "push", "Shoulders", ("Dumbbells",), ("Standard", "Seated", "Standing", "Tempo"), 61),
    Family("Close-Grip Press", "push", "Triceps", ("Barbell", "Smith Machine", "Dumbbells"), ("Standard", "Paused", "Tempo"), 66),
    Family("Skull Crusher", "push", "Triceps", ("EZ Bar", "Barbell", "Dumbbells", "Cable"), ("Standard", "Paused", "Tempo", "Controlled"), 60),
    Family("Cable Crossover", "push", "Chest", ("Cable",), ("Standard", "High-to-Low", "Low-to-High", "Controlled"), 59),

    Family("Row", "pull", "Mid Back", ("Barbell", "Dumbbells", "Cable", "Machine", "Landmine", "Band"), ("Standard", "Single-Arm", "Seated", "Standing", "Paused", "Tempo", "Wide-Stance", "Narrow-Stance"), 82),
    Family("Pull-Up", "pull", "Lats", ("Bodyweight", "Band", "Suspension Trainer"), ("Standard", "Paused", "Tempo", "Explosive", "Controlled"), 79),
    Family("Chin-Up", "pull", "Lats", ("Bodyweight", "Band"), ("Standard", "Paused", "Tempo", "Controlled"), 77),
    Family("Lat Pulldown", "pull", "Lats", ("Cable", "Machine", "Band"), ("Standard", "Wide-Stance", "Narrow-Stance", "Single-Arm", "Paused", "Tempo"), 74),
    Family("Deadlift", "pull", "Posterior Chain", ("Barbell", "Trap Bar", "Dumbbells", "Kettlebell", "Smith Machine", "Sandbag"), ("Standard", "Paused", "Tempo", "Deficit", "Wide-Stance", "Narrow-Stance"), 85),
    Family("Romanian Deadlift", "pull", "Hamstrings", ("Barbell", "Dumbbells", "Kettlebell", "Smith Machine", "Trap Bar"), ("Standard", "Single-Leg", "Paused", "Tempo", "Deficit"), 80),
    Family("Good Morning", "pull", "Hamstrings", ("Barbell", "Band", "Smith Machine", "Sandbag"), ("Standard", "Paused", "Tempo", "Controlled"), 65),
    Family("Back Extension", "pull", "Lower Back", ("Bodyweight", "Dumbbells", "Barbell", "Machine"), ("Standard", "Paused", "Tempo", "Controlled"), 63),
    Family("Face Pull", "pull", "Rear Delts", ("Cable", "Band"), ("Standard", "Paused", "Tempo", "Controlled"), 67),
    Family("Rear Delt Fly", "pull", "Rear Delts", ("Dumbbells", "Cable", "Machine", "Band"), ("Standard", "Seated", "Single-Arm", "Paused", "Tempo"), 62),
    Family("Shrug", "pull", "Traps", ("Barbell", "Dumbbells", "Trap Bar", "Machine", "Smith Machine"), ("Standard", "Paused", "Tempo", "Controlled"), 60),
    Family("Biceps Curl", "pull", "Biceps", ("Dumbbells", "Barbell", "EZ Bar", "Cable", "Band", "Machine"), ("Standard", "Alternating", "Seated", "Standing", "Single-Arm", "Tempo", "Paused"), 64),
    Family("Hammer Curl", "pull", "Biceps", ("Dumbbells", "Cable", "Band", "EZ Bar"), ("Standard", "Alternating", "Single-Arm", "Seated", "Tempo"), 60),
    Family("High Pull", "pull", "Upper Back", ("Barbell", "Dumbbells", "Kettlebell", "Cable"), ("Standard", "Explosive", "Paused", "Tempo"), 62),

    Family("Squat", "legs", "Quads", ("Bodyweight", "Barbell", "Dumbbells", "Kettlebell", "Machine", "Smith Machine", "Sandbag", "Trap Bar"), ("Standard", "Paused", "Tempo", "Front", "Back", "Wide-Stance", "Narrow-Stance", "Deficit"), 86),
    Family("Split Squat", "legs", "Quads", ("Bodyweight", "Dumbbells", "Barbell", "Kettlebell", "Smith Machine", "Sandbag"), ("Standard", "Paused", "Tempo", "Rear-Foot-Elevated", "Front-Foot-Elevated", "Single-Leg"), 81),
    Family("Lunge", "legs", "Quads", ("Bodyweight", "Dumbbells", "Barbell", "Kettlebell", "Sandbag"), ("Standard", "Walking", "Reverse", "Alternating", "Tempo", "Paused"), 79),
    Family("Step-Up", "legs", "Quads", ("Bodyweight", "Dumbbells", "Barbell", "Kettlebell", "Sandbag"), ("Standard", "Alternating", "Single-Leg", "Tempo", "Paused"), 74),
    Family("Leg Press", "legs", "Quads", ("Machine", "Smith Machine"), ("Standard", "Wide-Stance", "Narrow-Stance", "Single-Leg", "Paused", "Tempo"), 73),
    Family("Leg Extension", "legs", "Quads", ("Machine", "Band", "Cable"), ("Standard", "Single-Leg", "Paused", "Tempo", "Controlled"), 67),
    Family("Leg Curl", "legs", "Hamstrings", ("Machine", "Band", "Cable", "Stability Ball"), ("Standard", "Single-Leg", "Paused", "Tempo", "Controlled"), 70),
    Family("Nordic Curl", "legs", "Hamstrings", ("Bodyweight", "Band"), ("Standard", "Assisted", "Tempo", "Paused"), 72),
    Family("Hip Thrust", "legs", "Glutes", ("Barbell", "Dumbbells", "Machine", "Band", "Smith Machine", "Sandbag"), ("Standard", "Single-Leg", "Paused", "Tempo", "Controlled"), 78),
    Family("Glute Bridge", "legs", "Glutes", ("Bodyweight", "Barbell", "Dumbbells", "Band", "Sandbag"), ("Standard", "Single-Leg", "Paused", "Tempo", "Isometric"), 70),
    Family("Calf Raise", "legs", "Calves", ("Bodyweight", "Dumbbells", "Barbell", "Machine", "Smith Machine"), ("Standard", "Seated", "Standing", "Single-Leg", "Paused", "Tempo"), 66),
    Family("Hack Squat", "legs", "Quads", ("Machine", "Smith Machine", "Barbell"), ("Standard", "Paused", "Tempo", "Narrow-Stance", "Wide-Stance"), 72),
    Family("Cossack Squat", "legs", "Adductors", ("Bodyweight", "Kettlebell", "Dumbbells", "Sandbag"), ("Standard", "Paused", "Tempo", "Controlled"), 60),
    Family("Box Squat", "legs", "Quads", ("Barbell", "Dumbbells", "Kettlebell", "Smith Machine"), ("Standard", "Paused", "Tempo", "Wide-Stance"), 71),
    Family("Sled Sprint", "legs", "Conditioning", ("Sled",), ("Standard", "Explosive", "Tempo", "Heavy"), 64),

    Family("Plank", "core", "Core", ("Bodyweight", "Band", "Suspension Trainer"), ("Standard", "Side", "Reverse", "Isometric", "Tempo"), 76),
    Family("Dead Bug", "core", "Core", ("Bodyweight", "Band", "Dumbbells"), ("Standard", "Alternating", "Tempo", "Isometric"), 72),
    Family("Bird Dog", "core", "Core", ("Bodyweight", "Band", "Dumbbells"), ("Standard", "Alternating", "Tempo", "Paused"), 69),
    Family("Pallof Press", "core", "Core", ("Cable", "Band"), ("Standard", "Standing", "Half-Kneeling", "Isometric", "Tempo"), 73),
    Family("Crunch", "core", "Abs", ("Bodyweight", "Cable", "Machine", "Band"), ("Standard", "Reverse", "Decline", "Tempo", "Paused"), 66),
    Family("Hanging Knee Raise", "core", "Abs", ("Bodyweight", "Band"), ("Standard", "Tempo", "Paused", "Controlled"), 68),
    Family("Hanging Leg Raise", "core", "Abs", ("Bodyweight",), ("Standard", "Tempo", "Paused", "Controlled"), 67),
    Family("Ab Wheel Rollout", "core", "Abs", ("Bodyweight", "Band"), ("Standard", "Paused", "Tempo", "Controlled"), 70),
    Family("Russian Twist", "core", "Obliques", ("Bodyweight", "Medicine Ball", "Dumbbells", "Kettlebell"), ("Standard", "Alternating", "Tempo", "Paused"), 64),
    Family("Cable Wood Chop", "core", "Obliques", ("Cable", "Band"), ("Standard", "Standing", "Half-Kneeling", "Tempo"), 65),

    Family("Intervals", "cardio", "Conditioning", ("Bike", "Rower", "Treadmill", "Elliptical", "Stairs"), ("Standard", "Explosive", "Tempo", "Controlled"), 72),
    Family("Steady-State Cardio", "cardio", "Conditioning", ("Bike", "Rower", "Treadmill", "Elliptical", "Stairs"), ("Standard", "Tempo", "Controlled"), 68),
    Family("Jump Rope", "cardio", "Conditioning", ("Bodyweight",), ("Standard", "Alternating", "Explosive", "Tempo"), 65),
    Family("Burpee", "cardio", "Conditioning", ("Bodyweight",), ("Standard", "Explosive", "Tempo", "Controlled"), 63),
    Family("Mountain Climber", "cardio", "Conditioning", ("Bodyweight",), ("Standard", "Alternating", "Explosive", "Tempo"), 62),

    Family("Carry", "other", "Grip", ("Dumbbells", "Kettlebell", "Sandbag", "Trap Bar", "Barbell"), ("Farmer", "Suitcase", "Overhead", "Front-Rack", "Alternating"), 74),
    Family("Turkish Get-Up", "other", "Full Body", ("Kettlebell", "Dumbbells", "Sandbag"), ("Standard", "Paused", "Tempo", "Controlled"), 70),
    Family("Medicine Ball Slam", "other", "Conditioning", ("Medicine Ball",), ("Standard", "Explosive", "Alternating", "Tempo"), 62),
    Family("Battle Rope Slam", "other", "Conditioning", ("Battle Rope",), ("Standard", "Alternating", "Explosive", "Tempo"), 60),
)


def clean_name(name: str) -> str:
    return " ".join(name.replace("  ", " ").strip().split())


def build_name(variation: str, equipment: str, base: str) -> str:
    if variation == "Standard":
        if equipment == "Bodyweight":
            return base if "Bodyweight" not in base else base
        return f"{equipment} {base}"

    directional_like = {
        "Farmer",
        "Suitcase",
        "Overhead",
        "Front-Rack",
        "High-to-Low",
        "Low-to-High",
        "Rear-Foot-Elevated",
        "Front-Foot-Elevated",
        "Walking",
        "Heavy",
        "Assisted",
        "Side",
        "Reverse",
        "Overhead",
        "Half-Kneeling",
        "Front",
        "Back",
        "Seated",
        "Standing",
    }

    if equipment == "Bodyweight":
        if variation in directional_like:
            return f"{variation} {base}"
        return f"{variation} {base}"

    if variation in directional_like:
        return f"{variation} {equipment} {base}"
    return f"{variation} {equipment} {base}"


def build_description(name: str, muscle_group: str, equipment: str) -> str:
    return (
        f"{name} targeting {muscle_group.lower()} with {equipment.lower()} to improve strength,"
        " control, and movement quality."
    )


def curated_candidates() -> Iterable[Candidate]:
    for name, category, equipment, muscle_group in CURATED_CORE:
        yield Candidate(
            name=name,
            category=category,
            equipment=equipment,
            muscle_group=muscle_group,
            default_tempo=CATEGORY_TEMPO[category],
            description=build_description(name, muscle_group, equipment),
            score=999,
        )


def family_candidates() -> Iterable[Candidate]:
    for family in FAMILIES:
        for equipment in family.equipments:
            for variation in family.variations:
                name = clean_name(build_name(variation, equipment, family.base))
                if len(name) > 255:
                    continue

                score = family.base_score + EQUIPMENT_SCORE.get(equipment, 10) + VARIATION_SCORE.get(variation, 10)
                yield Candidate(
                    name=name,
                    category=family.category,
                    equipment=equipment,
                    muscle_group=family.muscle_group,
                    default_tempo=CATEGORY_TEMPO[family.category],
                    description=build_description(name, family.muscle_group, equipment),
                    score=score,
                )


def build_ranked_candidate_pool() -> list[Candidate]:
    pool = list(curated_candidates()) + list(family_candidates())

    dedup: dict[str, Candidate] = {}
    for candidate in pool:
        key = candidate.name.lower()
        existing = dedup.get(key)
        if not existing or candidate.score > existing.score:
            dedup[key] = candidate

    ranked = sorted(dedup.values(), key=lambda c: (-c.score, c.name))
    return ranked


def main() -> None:
    db = SessionLocal()
    try:
        existing_names = {name.lower() for (name,) in db.execute(select(Exercise.name)).all()}
        current_total = len(existing_names)
        remaining_to_insert = max(0, TARGET_TOTAL_EXERCISES - current_total)

        if remaining_to_insert == 0:
            print(f"No insert needed. Total exercises already at {current_total}.")
            return

        ranked = build_ranked_candidate_pool()
        selected: list[Candidate] = []
        selected_keys: set[str] = set()

        for candidate in ranked:
            key = candidate.name.lower()
            if key in existing_names or key in selected_keys:
                continue
            selected.append(candidate)
            selected_keys.add(key)
            if len(selected) >= remaining_to_insert:
                break

        filler_index = 1
        while len(selected) < remaining_to_insert:
            name = f"General Strength Drill {filler_index}"
            key = name.lower()
            filler_index += 1
            if key in existing_names or key in selected_keys:
                continue
            selected.append(
                Candidate(
                    name=name,
                    category="other",
                    equipment="Bodyweight",
                    muscle_group="Conditioning",
                    default_tempo=CATEGORY_TEMPO["other"],
                    description="General full-body conditioning drill for movement practice and work capacity.",
                    score=1,
                )
            )
            selected_keys.add(key)

        db.add_all(
            [
                Exercise(
                    name=c.name,
                    category=c.category,
                    equipment=c.equipment,
                    muscle_group=c.muscle_group,
                    default_tempo=c.default_tempo,
                    description=c.description,
                    created_by_trainer_id=None,
                )
                for c in selected
            ]
        )
        db.commit()

        total_exercises = db.scalar(select(func.count(Exercise.id))) or 0
        print(f"Inserted {len(selected)} global exercises.")
        print(f"Total exercises in bank: {total_exercises}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
