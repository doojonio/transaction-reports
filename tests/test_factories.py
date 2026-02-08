from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transactions import Transaction
from app.models.users import User
from tests.factories import TransactionFactory, UserFactory


async def test_factories(db: AsyncSession):
    user = await UserFactory()
    transaction = await TransactionFactory(user=user)
    transaction2 = await TransactionFactory(user=user)

    assert user.id is not None
    assert transaction.id is not None
    assert transaction2.id is not None

    users = (await db.execute(select(User))).scalars().all()
    transactions = (await db.execute(select(Transaction))).scalars().all()
    assert len(users) == 1
    assert len(transactions) == 2

    assert users[0].id == user.id

    transaction_ids = {tr.id for tr in [transaction, transaction2]}
    assert {tr.id for tr in transactions} == transaction_ids
