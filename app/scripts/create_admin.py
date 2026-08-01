import asyncio
import getpass
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.domain import Officer
from app.models.enums import OfficerRole
from app.core.security import hash_password

async def create_first_admin():
    async with AsyncSessionLocal() as db:
        # Guard: don't create a second admin by accident
        existing_admin = await db.execute(
            select(Officer).where(Officer.role == OfficerRole.ADMIN)
        )
        if existing_admin.scalar_one_or_none():
            print("An admin already exists. Aborting to avoid duplicates.")
            return

        name = input("Admin name: ")
        email = input("Admin email: ")
        password = getpass.getpass("Admin password: ")

        # Guard: don't collide with an existing email
        existing_email = await db.execute(
            select(Officer).where(Officer.email == email)
        )
        if existing_email.scalar_one_or_none():
            print(f"An officer with email {email} already exists. Aborting.")
            return

        new_admin = Officer(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            role=OfficerRole.ADMIN,
        )
        db.add(new_admin)
        await db.commit()
        print(f"Admin created: {email}")

if __name__ == "__main__":
    asyncio.run(create_first_admin())


