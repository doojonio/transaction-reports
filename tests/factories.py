import factory
import factory.alchemy

from app.models import Transaction, User
from app.models.transactions import TransactionStatus, TransactionType
from tests.conftest import async_session


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = async_session

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)
        await async_session.commit()
        return instance


class UserFactory(BaseFactory):
    class Meta:
        model = User

    id = factory.Faker("uuid4")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    created_at = factory.Faker("date_time_between", start_date="-2y", end_date="now")
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class TransactionFactory(BaseFactory):
    class Meta:
        model = Transaction

    id = factory.Faker("uuid4")
    # subfactories do not work with async session
    user = factory.SubFactory(UserFactory)
    sum = factory.Faker("pydecimal", left_digits=13, right_digits=2, positive=True)
    status = factory.Faker("random_element", elements=list(TransactionStatus))
    type = factory.Faker("random_element", elements=list(TransactionType))
    created_at = factory.Faker("date_time_between", start_date="-2y", end_date="now")
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)
