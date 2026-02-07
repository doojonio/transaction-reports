from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, User
from tests.factories import TransactionFactory, UserFactory


async def test_factories(db: AsyncSession):
    user = await UserFactory()
    transaction = await TransactionFactory(user=user)
    transaction2 = await TransactionFactory(user=user)

    assert user.id is not None
    assert transaction.id is not None
    assert transaction2.id is not None

    users = (await db.execute(select(User))).all()
    transactions = (await db.execute(select(Transaction))).all()
    print(users)
    print(transactions)
