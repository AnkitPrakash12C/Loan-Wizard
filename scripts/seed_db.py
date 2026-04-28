"""
scripts/seed_db.py
Initialize the database tables.
Run once before starting the server:
    python scripts/seed_db.py
"""
import asyncio
import sys
from pathlib import Path

# Make sure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import create_tables


async def main():
    print("Creating database tables …")
    await create_tables()
    print("Done. Tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
