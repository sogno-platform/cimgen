from pydantic import ConfigDict

# Used to configure pydantic dataclasses.

# See doc at
# https://docs.pydantic.dev/latest/usage/model_config/#options
cgmes_resource_config :ConfigDict = {
    # By default, with pydantic extra arguments given to a dataclass are silently ignored.
    # This matches the default behaviour by failing noisily.
    "extra" : "forbid"
}
