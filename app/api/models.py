from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel):
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")


class Meta(BaseModel):
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[str] = Field(None, description="Success or error message")
    errors: Optional[List[str]] = Field(None, description="Error details (only for 4xx/5xx)")
    pagination: Optional[Pagination] = Field(
        None, description="Pagination information (for list endpoints)"
    )


class Response(BaseModel, Generic[T]):
    data: T = Field(..., description="Response data")
    meta: Meta = Field(..., description="Metadata about the response")


class SuccessResponse(Response[T]):
    @classmethod
    def create(
        cls,
        data: T,
        status_code: int = 200,
        details: Optional[str] = None,
        pagination: Optional[Pagination] = None,
    ):
        return cls(
            data=data,
            meta=Meta(
                status_code=status_code,
                details=details or "Success",
                pagination=pagination,
            ),
        )


class ErrorResponse(BaseModel):
    data: Optional[dict] = Field(None, description="Response data (null for errors)")
    meta: Meta = Field(..., description="Metadata about the error")

    @classmethod
    def create(cls, status_code: int, details: str, errors: Optional[List[str]] = None):
        return cls(
            data=None,
            meta=Meta(status_code=status_code, details=details, errors=errors),
        )
