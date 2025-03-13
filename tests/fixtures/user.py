import pytest

from examples.api_for_sqlalchemy.schemas import UserAttributesBaseSchema
from tests.misc.utils import fake


@pytest.fixture
def user_attributes_factory():
    def factory():
        user_attributes = UserAttributesBaseSchema(
            name=fake.name(),
            age=fake.pyint(min_value=13, max_value=99),
            email=fake.email(),
        )
        return user_attributes

    return factory


@pytest.fixture
def user_attributes(user_attributes_factory):
    return user_attributes_factory()
