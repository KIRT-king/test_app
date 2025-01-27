import asyncio

from db.commands import init_db, create_user, get_user, delete_user, update_user_last_enter
from db.models import User


async def main():
    pass
    # await init_db()
    # await create_user("kirt", "1", "1", "1", "1", "1")
    # # await update_user_last_enter("kirt")



if __name__ == "__main__":
    asyncio.run(main())