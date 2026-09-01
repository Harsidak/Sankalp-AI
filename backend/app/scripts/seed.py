"""
Seed the database with a demo account and ~60 days of plausible history.

Run it with:  python -m app.scripts.seed

The generated data is deliberately not uniform: mood follows a weekly
rhythm with noise, some days are skipped entirely, and habits have
realistic gaps. Flat or perfect data makes the dashboard look broken even
when it is working, and makes streak logic look untested.

The script is idempotent -- it wipes and rebuilds the demo user's rows on
each run, so it is safe to re-run while iterating on the frontend.
"""

import asyncio
import math
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal, engine, init_db
from app.core.security import hash_password
from app.models.user import AuthProvider, User
from app.models.wellness import (
    CheckIn,
    Habit,
    HabitLog,
    JournalEntry,
    Tag,
)

DEMO_EMAIL = "demo@sankalp.app"
DEMO_PASSWORD = "demo1234"
DAYS = 60

TAGS = [
    ("study", "#6366f1"),
    ("family", "#ec4899"),
    ("sleep", "#8b5cf6"),
    ("exercise", "#10b981"),
    ("stress", "#f59e0b"),
    ("friends", "#06b6d4"),
    ("gratitude", "#84cc16"),
]

HABITS = [
    ("Sleep by 11pm", "moon", "#8b5cf6", 7, 0.72),
    ("Walk 20 minutes", "activity", "#10b981", 5, 0.64),
    ("Read 10 pages", "book", "#6366f1", 5, 0.55),
    ("Drink 2L water", "droplet", "#06b6d4", 7, 0.81),
    ("No phone in bed", "phone-off", "#f59e0b", 6, 0.42),
]

# (title, body, tag names) - written to read like a real person, because
# lorem ipsum makes the journal UI impossible to judge.
ENTRIES = [
    ("Long lab day", "Spent six hours on the DBMS assignment. Frustrating for most of it, then the join finally clicked and it felt worth it.", ["study", "stress"]),
    ("Called home", "Mum asked about the project. Explained the whole thing and she pretended to follow. Felt lighter afterwards.", ["family", "gratitude"]),
    ("Bad night", "Woke up around 3 and could not get back to sleep. Everything felt heavier today because of it.", ["sleep", "stress"]),
    ("Ran in the morning", "Cold but clear. Did the long loop for the first time in weeks and did not stop once.", ["exercise"]),
    ("Coffee with A", "We talked for two hours. I did not realise how much I needed that until I was walking back.", ["friends", "gratitude"]),
    ("Deadline creeping", "Three things due next week and I keep opening the easiest one. Need to just start the hard one.", ["study", "stress"]),
    ("Small win", "Fixed the bug that had been bothering me since Tuesday. It was a typo. Of course it was.", ["study"]),
    ("Quiet Sunday", "Did almost nothing on purpose. Cooked properly instead of eating at the desk.", ["gratitude"]),
    ("Skipped the gym again", "Third time this week. Not going to spiral about it, just going to go tomorrow.", ["exercise", "stress"]),
    ("Good sleep finally", "Eight hours straight. Woke up before the alarm and everything was easier.", ["sleep", "gratitude"]),
    ("Group project friction", "Nobody had done their part. Said something about it, which I usually avoid doing.", ["study", "stress", "friends"]),
    ("Walk after dinner", "Went out at nine when it was cool. Thought about nothing in particular, which was the point.", ["exercise", "sleep"]),
    ("Dad's birthday", "Everyone on the call at once, all talking over each other. It was chaos and it was good.", ["family", "gratitude"]),
    ("Overthinking again", "Replayed a two-minute conversation for an hour. Trying to notice when I start doing that.", ["stress"]),
    ("Back on track", "Two solid study blocks, no phone. Proof that the mornings work better than the nights.", ["study"]),
    ("Rainy and slow", "Low energy all day and did not fight it. Read on the sofa instead.", ["sleep"]),
    ("Cooked for friends", "Made way too much food. Everyone stayed until midnight.", ["friends", "gratitude"]),
    ("Presentation done", "Nervous beforehand, fine during, relieved after. The usual sequence.", ["study"]),
]


def _mood_for(day_index: int, rng: random.Random) -> tuple[int, int]:
    """
    Generate a (mood, energy) pair with a weekly rhythm plus noise.

    A slow upward drift across the window gives the trend line something
    honest to show, rather than pure noise around a flat mean.
    """
    weekly = math.sin((day_index / 7.0) * 2 * math.pi)
    drift = day_index / DAYS  # gentle improvement over the window

    mood = 3.1 + 0.55 * weekly + 0.7 * drift + rng.gauss(0, 0.55)
    energy = mood + rng.gauss(-0.15, 0.5)

    clamp = lambda v: max(1, min(5, int(round(v))))
    return clamp(mood), clamp(energy)


async def seed() -> None:
    """Build the demo account and its history."""
    rng = random.Random(20260831)  # fixed seed - reruns produce the same data

    await init_db()

    async with AsyncSessionLocal() as db:
        # --- demo user -------------------------------------------------
        result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()

        if user:
            print(f"Rebuilding data for existing user {DEMO_EMAIL}")
            # Wipe the wellness rows. entry_tags and habit_logs follow via
            # ON DELETE CASCADE, so they are not deleted explicitly.
            for model in (CheckIn, JournalEntry, Tag, Habit):
                await db.execute(delete(model).where(model.user_id == user.id))
        else:
            print(f"Creating user {DEMO_EMAIL}")
            user = User(
                email=DEMO_EMAIL,
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name="Demo User",
                is_active=True,
                is_verified=True,
                auth_provider=AuthProvider.LOCAL,
            )
            db.add(user)
            await db.flush()

        today = date.today()
        start = today - timedelta(days=DAYS - 1)

        # --- tags ------------------------------------------------------
        tags = {}
        for name, color in TAGS:
            tag = Tag(user_id=user.id, name=name, color=color)
            db.add(tag)
            tags[name] = tag
        await db.flush()

        # --- check-ins -------------------------------------------------
        checkin_count = 0
        for i in range(DAYS):
            day = start + timedelta(days=i)
            # Roughly one day in seven is missed, so the chart has real gaps.
            if rng.random() < 0.14:
                continue

            mood, energy = _mood_for(i, rng)
            db.add(
                CheckIn(
                    user_id=user.id,
                    mood_score=mood,
                    energy_score=energy,
                    checkin_date=day,
                    note=None,
                )
            )
            checkin_count += 1

        # --- journal entries -------------------------------------------
        entry_days = sorted(rng.sample(range(DAYS), k=min(len(ENTRIES), DAYS)))
        for offset, (title, body, tag_names) in zip(entry_days, ENTRIES):
            day = start + timedelta(days=offset)
            created = datetime.combine(
                day,
                datetime.min.time().replace(hour=rng.randint(8, 22)),
                tzinfo=timezone.utc,
            )
            entry = JournalEntry(
                user_id=user.id,
                title=title,
                content=body,
                created_at=created,
                updated_at=created,
            )
            entry.tags = [tags[n] for n in tag_names if n in tags]
            db.add(entry)

        # --- habits and their logs -------------------------------------
        log_count = 0
        for name, icon, color, target, rate in HABITS:
            habit = Habit(
                user_id=user.id,
                name=name,
                icon=icon,
                color=color,
                target_per_week=target,
                # Backdated to the start of the window, because the logs below
                # are. A habit created "now" with two months of history behind
                # it is incoherent, and the insights queries measure a habit
                # from when tracking began.
                created_at=datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc),
            )
            db.add(habit)
            await db.flush()

            for i in range(DAYS):
                day = start + timedelta(days=i)
                # Habits get easier to keep as the window progresses, which
                # produces streaks worth rendering instead of uniform noise.
                chance = rate * (0.75 + 0.45 * (i / DAYS))
                if rng.random() < min(chance, 0.95):
                    db.add(HabitLog(habit_id=habit.id, completed_date=day))
                    log_count += 1

        await db.commit()

    await engine.dispose()  # aiomysql raises at exit if the loop closes first

    print(
        f"Seeded {checkin_count} check-ins, {len(ENTRIES)} journal entries, "
        f"{len(TAGS)} tags, {len(HABITS)} habits, {log_count} habit logs "
        f"across {DAYS} days."
    )
    print(f"Log in with  {DEMO_EMAIL}  /  {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
