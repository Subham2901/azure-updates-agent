""" Typed Schemas for Azure update records
Every record in a report MUST originate from a validated AzureUpdate instance parsed from MRC MCP server output.
 No other data path exists.

"""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl,field_validator

class UpdateStatus(StrEnum):
    """Lifecyle status of an Azure update, as reported by Microsoft."""
    IN_DEVELOPMENT = "In development"
    IN_PREVIEW="In preview"
    LAUNCHED = "Launched"
    UNKNOWN="Unknown" # Forward-comatibility fallback
class AzureUpdate(BaseModel):
    """ A single Azure Update record from the MRC MCP server.
    Field names mirror the upstream payload so a reviewer can diff this schema against Microsoft's documented response shape."""
    model_config= ConfigDict(frozen=True) #immutable once parsed
    id:str=Field(min_length=1)
    title:str=Field(min_length=1)
    description : str =""
    status:UpdateStatus=UpdateStatus.UNKNOWN
    products: tuple[str,...]=()
    tags:tuple[str,...]=()
    created: datetime|None=None
    modified: datetime|None=None
    link:HttpUrl|None=None

    @field_validator("status",mode="before")
    @classmethod
    def _coerce_unknown_status(cls, v:object)->object:
        """Map unrecognised status strings to UNKNOWN instead of failing.
        New  vocabulary from Microsoft should degrade gracefully;
        structual problems (missing id/title) should still fail hard."""

        if isinstance(v,str) and v not in UpdateStatus:
            return UpdateStatus.UNKNOWN
        return v
    


    