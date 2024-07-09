import typing
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, create_model

CUSTOM_FIELDS = {"option": typing.Literal}


def get_model_from_file(file_path: str | Path) -> type[BaseModel]:
    """
    Return Pydantic schema from a YAML file.

    Replaces types of `CUSTOM_FIELDS` with the definitions, other types are evaluated
    as primitive Python type.

    Args:
        - file_path: Path of the YAML file.
    """
    with open(file_path, "r") as file:
        schema = yaml.safe_load(file)

    fields: dict[str, typing.Any] = {}
    for field_name, field_info in schema["fields"].items():
        f_type_raw = field_info.pop("type")
        f_type = CUSTOM_FIELDS.get(f_type_raw)

        if f_type is None:  # not custom definition, can be evaluated as primitive type
            field_type = eval(f_type_raw)
        else:
            field_type = f_type

        if field_type == typing.Literal:
            field_type = typing.Literal[tuple(field_info["values"])]

        fields[field_name] = (field_type, Field(**field_info))

    PydanticSchema = create_model("ParsePydanticSchema", **fields)
    return PydanticSchema
