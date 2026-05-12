from typing import Annotated

from pydantic import BaseModel, Field

CleanText = Annotated[str, Field(min_length=1, max_length=5000)]


class ErrorResponse(BaseModel):
    error: str = Field(..., examples=["unauthorized"])
    message: str = Field(..., examples=["Invalid or missing X-Api-Key header."])


class SentimentRequest(BaseModel):
    text: CleanText = Field(..., examples=["I love this!"])


class SentimentResult(BaseModel):
    label: str = Field(..., examples=["POSITIVE"])
    score: float = Field(..., ge=0.0, le=1.0, examples=[0.9998])


class SentimentResponse(BaseModel):
    text: str
    sentiment: SentimentResult
    model: str


class BatchSentimentRequest(BaseModel):
    texts: list[CleanText] = Field(..., min_length=1, max_length=32)


class BatchSentimentItem(BaseModel):
    text: str
    sentiment: SentimentResult


class BatchSentimentResponse(BaseModel):
    results: list[BatchSentimentItem]
    model: str
    count: int
