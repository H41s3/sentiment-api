from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

# Shared type alias applied to every user-supplied text field.
# Pydantic enforces these bounds at parse time, before any route handler runs.
CleanText = Annotated[str, Field(min_length=1, max_length=5000)]


class ErrorResponse(BaseModel):
    """Canonical error shape returned on all 4xx/5xx responses.

    Documenting this in the schema ensures Swagger UI shows the exact JSON
    structure that clients will receive on failure — not just a generic 422.
    """

    error: str = Field(..., examples=["unauthorized"])
    message: str = Field(..., examples=["Invalid or missing X-Api-Key header."])


class SentimentRequest(BaseModel):
    text: CleanText = Field(..., examples=["I love this!"])

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank or whitespace only")
        return v


class SentimentResult(BaseModel):
    label: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"] = Field(..., examples=["POSITIVE"])
    # score is the model's confidence, not a sentiment polarity score.
    # A NEGATIVE result with score=0.99 means the model is 99% confident it's negative.
    score: float = Field(..., ge=0.0, le=1.0, examples=[0.9998])


class SentimentResponse(BaseModel):
    text: str
    sentiment: SentimentResult
    model: str
    processing_ms: float = Field(..., description="Time spent on inference in milliseconds")


class BatchSentimentRequest(BaseModel):
    texts: list[CleanText] = Field(..., min_length=1)
    # Upper bound is enforced in the route handler against settings.max_batch_size
    # so operators can tune it via MAX_BATCH_SIZE without a code change or redeploy.


class BatchSentimentItem(BaseModel):
    text: str
    sentiment: SentimentResult


class BatchSentimentResponse(BaseModel):
    results: list[BatchSentimentItem]
    model: str
    count: int
    processing_ms: float = Field(..., description="Time spent on batch inference in milliseconds")


class ModelInfoResponse(BaseModel):
    model: str
    max_length: int
    max_batch_size: int
    version: str
    inference_count: int = Field(
        ..., description="Total texts classified by this worker since startup"
    )
