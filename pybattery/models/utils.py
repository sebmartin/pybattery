from dataclasses import fields, is_dataclass
from typing import TypeVar, Type, get_origin, get_args

T = TypeVar("T")


def from_dict(cls: Type[T], data: dict) -> T:
    if not is_dataclass(cls):
        raise TypeError(f"Expected a dataclass, got {cls}")

    fieldtypes = {f.name: f.type for f in fields(cls)}
    extras = {k: v for k, v in data.items() if k not in fieldtypes.keys()}
    kwargs = {}
    for field_name, field_type in fieldtypes.items():
        value = data.get(field_name)

        if value is None and field_name == "args" and extras:
            value = extras

        if value is None:
            kwargs[field_name] = None
            continue

        origin = get_origin(field_type)
        args = get_args(field_type)

        # Handle List[SomeDataclass]
        if origin is list and is_dataclass(args[0]):
            kwargs[field_name] = [from_dict(args[0], item) for item in value]  # type: ignore
        # Handle Dict[str, SomeDataclass]
        elif origin is dict and is_dataclass(args[1]):
            kwargs[field_name] = {k: from_dict(args[1], v) for k, v in value.items()}  # type: ignore
        # Handle nested dataclass
        elif is_dataclass(field_type):
            kwargs[field_name] = from_dict(field_type, value)  # type: ignore
        else:
            kwargs[field_name] = value

    return cls(**kwargs)
