from dataclasses import dataclass
from typing import Generic, TypeVar, Union, cast

# noinspection PyProtectedMember
from pydantic.fields import FieldInfo
from sqlalchemy import func
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.expression import BinaryExpression, BooleanClauseList

ColumnType = TypeVar("ColumnType")
ExpressionType = TypeVar("ExpressionType")


@dataclass(frozen=True)
class CustomFilterSQL(Generic[ColumnType, ExpressionType]):
    op: str

    def get_expression(
        self,
        schema_field: FieldInfo,
        model_column: ColumnType,
        value: str,
        operator: str,
    ) -> ExpressionType:
        raise NotImplementedError


class CustomFilterSQLA(CustomFilterSQL[InstrumentedAttribute, Union[BinaryExpression, BooleanClauseList]]):
    """Base class for custom SQLAlchemy filters"""


class LowerEqualsFilterSQL(CustomFilterSQLA):
    def get_expression(
        self,
        schema_field: FieldInfo,
        model_column: InstrumentedAttribute,
        value: str,
        operator: str,
    ) -> BinaryExpression:
        return cast(
            BinaryExpression,
            func.lower(model_column) == func.lower(value),
        )


# TODO: tests coverage
class JSONBContainsFilterSQL(CustomFilterSQLA):
    def get_expression(
        self,
        schema_field: FieldInfo,
        model_column: InstrumentedAttribute,
        value: str,
        operator: str,
    ) -> BinaryExpression:
        return model_column.op("@>")(value)


sql_filter_lower_equals = LowerEqualsFilterSQL(op="lower_equals")
sql_filter_jsonb_contains = JSONBContainsFilterSQL(op="jsonb_contains")
