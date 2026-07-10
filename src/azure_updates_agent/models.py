""" Typed Schemas for Azure update records
Every record in a report MUST originate from a validated AzureUpdate instance parsed from MRC MCP server output.
 No other data path exists.

"""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl,field_validator
from pydantic.alias_generators import to_camel

class Availability(BaseModel):
    """ One availability milestone (GA,Preview, Retirement) for an update"""
    model_config=ConfigDict(frozen=True)
    ring:str=""
    year:int |None=None
    month:str|None=None

class UpdateStatus(StrEnum):
    """Lifecyle status of an Azure update, as reported by Microsoft."""
    IN_DEVELOPMENT = "In development"
    IN_PREVIEW="In preview"
    LAUNCHED = "Launched"
    UNKNOWN="Unknown" # Forward-comatibility fallback
class AzureUpdate(BaseModel):
    """ A single Azure Update record from the MRC MCP server.

    Field names are snake_case internally; the alias generator maps them to Microsoft's camelCase payload at parse time."""
    model_config= ConfigDict(frozen=True,alias_generator=to_camel,populate_by_name=True,) #immutable once parsed
    
    id:str=Field(min_length=1)
    base_id:str=" "
    title:str=Field(min_length=1)
    description : str =""
    status:UpdateStatus=UpdateStatus.UNKNOWN
    products: tuple[str,...]=()
    product_categories:tuple[str,...]=()
    tags:tuple[str,...]=()
    availabilities:tuple[Availability,...]=()
    general_availability_date:str|None=None
    created: datetime|None=None
    modified: datetime|None=None

    @field_validator("status",mode="before")
    @classmethod
    def _coerce_unknown_status(cls, v:object)->object:
        """Map unrecognised status strings to UNKNOWN instead of failing.
        New  vocabulary from Microsoft should degrade gracefully;
        structual problems (missing id/title) should still fail hard."""

        if isinstance(v,str) and v not in UpdateStatus:
            return UpdateStatus.UNKNOWN
        return v
    @property
    def link(self)->str:
        """ DERIVED field : constructed from id, not present in source data."""
        return f"https://azure.microsoft.com/en-us/updates?id={self.id}"
class UpdatesPage(BaseModel):
    """ One page of the MRC response envelope (verified 2026-07-10)."""
    model_config= ConfigDict(frozen=True, alias_generator=to_camel, populate_by_name=True)
    items: tuple[AzureUpdate,...]=()
    total_count:int=0
    limit:int=0
    offset:int=0
    has_more:bool=False
    returned_count:int=0


    