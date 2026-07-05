from sqlalchemy import create_engine, text

from pipeline import config


def get_database_url() -> str:
    """Build the PostgreSQL connection URL from config settings."""
    return (
        f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}"
        f"@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"
    )


def get_engine():
    """Create and return a SQLAlchemy engine."""
    return create_engine(get_database_url())


def test_connection() -> bool:
    """Return True if the database accepts a simple query."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


if __name__ == "__main__":
    try:
        test_connection()
        print("Database connection successful.")
    except Exception as exc:
        print(f"Database connection failed: {exc}")
