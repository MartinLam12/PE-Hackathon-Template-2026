import csv
import os
from pathlib import Path

from app import create_app
from app.database import db
from app.models import Event, ShortURL, User

SEED_DIR = Path(os.environ.get("SEED_DIR", "seed_data"))


def load_csv(model, filename, fields):
    with (SEED_DIR / filename).open(newline="") as file:
        rows = csv.DictReader(file)
        model.insert_many(
            [{field: row[field] or None for field in fields} for row in rows]
        ).on_conflict_ignore().execute()


def seed():
    app = create_app()
    with app.app_context():
        db.connect(reuse_if_open=True)
        db.create_tables([User, ShortURL, Event])
        load_csv(User, "users.csv", ["id", "username", "email", "created_at"])
        load_csv(
            ShortURL,
            "urls.csv",
            [
                "id",
                "user_id",
                "short_code",
                "original_url",
                "title",
                "is_active",
                "created_at",
                "updated_at",
            ],
        )
        load_csv(
            Event,
            "events.csv",
            ["id", "url_id", "user_id", "event_type", "timestamp", "details"],
        )
        db.close()


if __name__ == "__main__":
    seed()
