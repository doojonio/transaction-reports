from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import tests.factories as f

USERS = 106
TRANSACTIONS = 112


async def mockfill(db: AsyncSession):
    if await _idempotence_check(db):
        return

    users = f.UserFactory.build_batch(100)
    db.add_all(users)
    await db.flush()
    for user in users:
        transactions = f.TransactionFactory.build_batch(
            100,
            user=user,
            created_at=f.factory.Faker(
                "date_time_between", start_date=user.created_at, end_date="now"
            ),
            updated_at=f.factory.Faker(
                "date_time_between", start_date=user.created_at, end_date="now"
            ),
        )
        db.add_all(transactions)
        await db.flush()

    await db.commit()


async def _idempotence_check(db: AsyncSession):
    stmt = text("SELECT EXISTS(select FROM users)")
    result = await db.execute(stmt)
    return result.scalar()
