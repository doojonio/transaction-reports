import uuid

import factory

from app.models.transactions import Transaction, TransactionStatus, TransactionType
from app.models.users import User
from tests.base_factory import BaseFactory


class UserFactory(BaseFactory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    external_id = factory.Sequence(lambda n: n + 1)
    created_at = factory.Faker("date_time_between", start_date="-2y", end_date="now")
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class TransactionFactory(BaseFactory):
    class Meta:
        model = Transaction

    id = factory.LazyFunction(uuid.uuid4)
    # subfactories do not work with async session
    user = factory.SubFactory(UserFactory)
    sum = factory.Faker("pydecimal", right_digits=2, min_value=1, max_value=1000)
    status = factory.Faker("random_element", elements=list(TransactionStatus))
    type = factory.Faker("random_element", elements=list(TransactionType))
    created_at = factory.Faker("date_time_between", start_date="-2y", end_date="now")
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)
