import asyncio
from db.database import create_tables

from db.models import Logs


async def main():
    await create_tables()

if __name__ == "__main__":
    asyncio.run(main())