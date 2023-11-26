class DataclassConfig:  # pylint: disable=too-few-public-methods
    """
    Used to configure pydantic dataclasses.

    See doc at
    https://docs.pydantic.dev/latest/usage/model_config/#options
    """

    # By default, with pydantic extra arguments given to a dataclass are silently ignored.
    # This matches the default behaviour by failing noisily.
    extra = "forbid"
    populate_by_name = True
    defer_build = True
    from_attributes = True

class GeoDataclassConfig:  # pylint: disable=too-few-public-methods
    """
    Used to configure pydantic dataclasses.

    See doc at
    https://docs.pydantic.dev/latest/usage/model_config/#options
    """

    # By default, with pydantic extra arguments given to a dataclass are silently ignored.
    # This matches the default behaviour by failing noisily.
    extra = "ignore"
    populate_by_name = True
    defer_build = True
    from_attributes = True
    arbitrary_types_allowed=True
