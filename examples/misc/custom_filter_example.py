from typing import Annotated, Optional

import orjson as json
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.expression import BinaryExpression

from fastapi_jsonapi.exceptions import InvalidFilters
from fastapi_jsonapi.types_metadata.custom_filter_sql import CustomFilterSQLA


def _get_sqlite_json_ilike_expression(
    model_column: InstrumentedAttribute,
    value: list,
    operator: str,
) -> BinaryExpression:
    try:
        target_field, regex = value
    except ValueError:
        msg = f'The "value" field has to be list of two values for op `{operator}`'
        raise InvalidFilters(msg)

    if isinstance(regex, (list, dict)):
        regex = json.dumps(regex).decode()
    elif isinstance(regex, bool):
        return model_column.op("->>")(target_field).is_(regex)
    else:
        regex = f"{regex}"

    return model_column.op("->>")(target_field).ilike(regex)


class SQLiteJSONIlikeFilterSQL(CustomFilterSQLA):
    def get_expression(
        self,
        schema_field: FieldInfo,
        model_column: InstrumentedAttribute,
        value: list[str],
        operator: str,
    ) -> BinaryExpression:
        return _get_sqlite_json_ilike_expression(model_column, value, operator)


sql_filter_sqlite_json_ilike = SQLiteJSONIlikeFilterSQL(op="sqlite_json_ilike")


class PictureSchema(BaseModel):
    """
    Now you can use `jsonb_contains` sql filter for this resource
    """

    name: str
    meta: Annotated[Optional[dict], sql_filter_sqlite_json_ilike] = Field(
        default_factory=dict,
        description="Any additional info in JSON format.",
        example={"location": "Moscow", "spam": "eggs"},
    )
