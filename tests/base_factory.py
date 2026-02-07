import factory.alchemy


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        session = BaseFactory._meta.sqlalchemy_session
        if session is None:
            raise RuntimeError(f"No session bound to {cls.__name__}")

        instance = model_class(*args, **kwargs)
        session.add(instance)
        await session.flush()
        return instance
