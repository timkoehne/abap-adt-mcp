"""Tool arguments with nested structure, passed to abap-adt-py as plain dicts."""

from typing import Any, Optional, Sequence, Union

from pydantic import BaseModel, Field


def plain(models: Optional[Sequence[BaseModel]]) -> Optional[list[dict[str, Any]]]:
    """The dicts abap-adt-py expects; fields left out stay out, so its defaults apply."""
    if models is None:
        return None
    return [model.model_dump(exclude_none=True) for model in models]


class FixedValue(BaseModel):
    low: str = Field(description="The value, or the lower limit of an interval")
    high: Optional[str] = Field(None, description="The upper limit of an interval")
    text: str = ""


class FieldLabels(BaseModel):
    short: Optional[str] = Field(None, description="At most 10 characters")
    medium: Optional[str] = Field(None, description="At most 20 characters")
    long: Optional[str] = Field(None, description="At most 40 characters")
    heading: Optional[str] = Field(None, description="At most 55 characters")


class Message(BaseModel):
    number: str = Field(description='Three digits, e.g. "001"')
    text: Optional[str] = Field(
        None, description="At most 73 characters, &1 to &4 are placeholders"
    )
    self_explanatory: Optional[bool] = Field(
        None, description="False if the message needs a long text, default True"
    )


class FilterCondition(BaseModel):
    filter: str = Field(description="Name of the BAdI filter")
    comparator: Optional[str] = Field(
        None, description="=, <>, <, <=, >, >=, CP (matches pattern) or NP; default ="
    )
    value: Optional[str] = None
    low: Optional[str] = Field(None, description="Range low <= filter <= high instead of value")
    high: Optional[str] = None


class BadiImplementation(BaseModel):
    name: str = Field(description="Name of this BAdI implementation")
    badi: str = Field(description="The BAdI definition it implements")
    implementing_class: str = Field(description="Class implementing the BAdI interface")
    description: Optional[str] = None
    active: Optional[bool] = Field(None, description="Default True")
    filters: Optional[
        list[Union[FilterCondition, list[Union[FilterCondition, list[FilterCondition]]]]]
    ] = Field(
        None,
        description="A flat list of conditions must all match. A list of lists is a list "
        "of alternatives (OR), each a list of conditions that all have to match (AND).",
    )

