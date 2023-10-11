from contextlib import contextmanager
from pydantic import (
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
)
from typing import Iterator, Any


def is_recursion_validation_error(exc: ValidationError) -> bool:
    errors = exc.errors()
    return len(errors) == 1 and errors[0]["type"] == "recursion_loop"


@contextmanager
def suppress_recursion_validation_error() -> Iterator[None]:
    try:
        yield
    except ValidationError as exc:
        if not is_recursion_validation_error(exc):
            raise exc


def cyclic_references_validator(
    v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
):
    try:
        return handler(v)
    except ValidationError as exc:
        if not (is_recursion_validation_error(exc) and isinstance(v, list)):
            raise exc

        value_without_cyclic_refs = []
        for child in v:
            with suppress_recursion_validation_error():
                value_without_cyclic_refs.extend(handler([child]))
        return handler(value_without_cyclic_refs)
