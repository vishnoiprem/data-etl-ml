"""Tag filters — the highest-risk piece of the whole project.

The Cost Explorer console's URL carries an operator that does not exist
in the API:

```
filter=[{dimension:{id:"TagKey"}, operator:"INCLUDES", values:["Data","Data-Squad"]}]
```

``INCLUDES`` is a **console-only** operator. The API's ``MatchOptions``
enum contains no such value — the valid set is ``EQUALS``, ``ABSENT``,
``STARTS_WITH``, ``ENDS_WITH``, ``CONTAINS``, ``CASE_SENSITIVE``,
``CASE_INSENSITIVE``, ``GREATER_THAN_OR_EQUAL``. An enum scan across
every ``ce`` input shape returns ``enums containing INCLUDE: NONE``.

So a tool that copies the console URL's operator into the API call
either errors outright or, worse, silently matches a different set of
tags and shows numbers that do not match the console the user was
looking at. The API equivalent of the console's ``TagKey INCLUDES
[...]`` is ``CONTAINS``.

This module exists so that translation happens in exactly one place, and
so that it is locked down by a fixture-equality test.

The two filters below are genuinely different questions, which is why
they are separate functions:

``build_tag_key_filter``
    Match on the **name** of a tag — "does this spend carry a tag whose
    key contains 'Data'?". This is the console's ``TagKey INCLUDES``.

``build_tag_value_filter``
    Match on the **value** a tag carries — "is this spend tagged
    ``team=data``?". This is ``Tag:Data``.
"""

from __future__ import annotations

from typing import Any

#: The console's operator. It has no API equivalent by that name.
CONSOLE_OPERATOR_INCLUDES = "INCLUDES"

#: The API's ``MatchOptions`` enum, in full. ``INCLUDES`` is absent.
VALID_MATCH_OPTIONS = (
    "EQUALS",
    "ABSENT",
    "STARTS_WITH",
    "ENDS_WITH",
    "CONTAINS",
    "CASE_SENSITIVE",
    "CASE_INSENSITIVE",
    "GREATER_THAN_OR_EQUAL",
)

#: The API equivalent of the console's ``INCLUDES``.
API_EQUIVALENT_OF_INCLUDES = "CONTAINS"

#: The dimension key used to match on a tag's *name*.
TAG_KEY_DIMENSION = "TagKey"


class TagFilterError(ValueError):
    """Raised when a tag filter cannot be built."""


def build_tag_key_filter(
    tag_keys: list[str],
    match: str = API_EQUIVALENT_OF_INCLUDES,
) -> dict[str, Any]:
    """A filter matching on the *names* of cost-allocation tags.

    This is the console's ``TagKey INCLUDES ["Data", "Data-Squad"]``.
    ``match`` defaults to ``CONTAINS`` — the API equivalent — because
    ``INCLUDES`` is not a valid API value and sending it would fail.

    ``CONTAINS`` on the tag *key* matches a tag named ``Data`` and a tag
    named ``Data-Squad`` and a tag named ``MyDataPipeline`` alike, which
    is what the console's ``INCLUDES`` does.
    """
    if not tag_keys:
        raise TagFilterError("build_tag_key_filter needs at least one tag key")

    _validate_match(match)

    return {
        "Tags": {
            "Key": TAG_KEY_DIMENSION,
            "Values": list(tag_keys),
            "MatchOptions": [match],
        }
    }


def build_tag_value_filter(
    tag_key: str,
    values: list[str],
    match: str = "EQUALS",
) -> dict[str, Any]:
    """A filter matching on the *value* a tag carries.

    This is the console's ``Tag:team`` dimension: spend where the tag
    ``team`` equals one of ``values``. It is a different question from
    the key filter, and it is the one that reproduces the "which squad
    spent this" view.
    """
    if not tag_key:
        raise TagFilterError("build_tag_value_filter needs a tag key")
    if not values:
        raise TagFilterError("build_tag_value_filter needs at least one value")

    _validate_match(match)

    return {
        "Tags": {
            "Key": tag_key,
            "Values": list(values),
            "MatchOptions": [match],
        }
    }


def _validate_match(match: str) -> None:
    """Reject an operator the API does not accept.

    ``INCLUDES`` is the one that matters — it is what a console URL
    hands you, and it is not in the enum. Failing loudly here beats
    failing at the API with a confusing error, or — far worse —
    silently matching something else.
    """
    if match.upper() == CONSOLE_OPERATOR_INCLUDES:
        raise TagFilterError(
            f"{CONSOLE_OPERATOR_INCLUDES!r} is a console-only operator and is not "
            f"valid in the Cost Explorer API. Use {API_EQUIVALENT_OF_INCLUDES!r} instead."
        )
    if match.upper() not in VALID_MATCH_OPTIONS:
        raise TagFilterError(
            f"{match!r} is not a valid MatchOptions value. "
            f"Valid values: {', '.join(VALID_MATCH_OPTIONS)}"
        )


def describe_filter(filter_spec: dict[str, Any]) -> str:
    """A one-line human description of a filter."""
    tags = filter_spec.get("Tags", {})
    key = tags.get("Key", "")
    values = tags.get("Values", [])
    match = (tags.get("MatchOptions") or ["EQUALS"])[0]
    joined = ", ".join(str(v) for v in values)
    if key == TAG_KEY_DIMENSION:
        return f"tag key {match} [{joined}]"
    return f"tag {key} {match} [{joined}]"
