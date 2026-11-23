
from app.src.database.database import Base, engine
from app.src.database.models import WebhookEvent


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    initialize_database()
