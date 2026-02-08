from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import tests.factories as f

USERS = 106
TRANSACTIONS = 112


async def mockfill(db: AsyncSession) -> None:
    """Seed the database with mock users and transactions.

    This function populates the database with a large set of realistic test
    data for development and testing purposes. It creates 100 users and, for
    each user, generates 100 transactions, totaling 10,000 transactions.

    The generated transactions are distributed over the last two years, with
    amounts, statuses, and types balanced according to the factory definitions.

    An idempotence check ensures that the database is only seeded once.

    Args:
        db: The asynchronous database session.
    """
    if await _idempotence_check(db):
        return

    users = f.UserFactory.build_batch(100)
    db.add_all(users)
    await db.flush()
    for user in users:
        transactions = f.TransactionFactory.build_batch(
            100,
            user=user,
            created_at=f.factory.Faker(  # type: ignore[attr-defined]
                "date_time_between", start_date=user.created_at, end_date="now"
            ),
            updated_at=f.factory.Faker(  # type: ignore[attr-defined]
                "date_time_between", start_date=user.created_at, end_date="now"
            ),
        )
        db.add_all(transactions)
        await db.flush()

    await db.commit()


async def _idempotence_check(db: AsyncSession) -> bool:
    """Check if db is already seeded."""
    stmt = text("SELECT EXISTS(select FROM users)")
    result = await db.execute(stmt)
    return bool(result.scalar())
