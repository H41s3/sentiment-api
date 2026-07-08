from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    "CleanText",
    "ErrorResponse",
    "SentimentRequest",
    "SentimentResult",
    "SentimentResponse",
    "BatchSentimentRequest",
    "BatchSentimentItem",
    "BatchSentimentResponse",
    "ModelInfoResponse",
]

# Shared type alias applied to every user-supplied text field.
# Pydantic enforces these bounds at parse time, before any route handler runs.
CleanText = Annotated[str, Field(min_length=1, max_length=5000)]


class ErrorResponse(BaseModel):
    """Canonical error shape returned on all 4xx/5xx responses.

    Documenting this in the schema ensures Swagger UI shows the exact JSON
    structure that clients will receive on failure — not just a generic 422.
    """

    error: str = Field(..., description="Machine-readable error code", examples=["unauthorized"])
    message: str = Field(
        ...,
        description="Human-readable error description",
        examples=["Invalid or missing X-Api-Key header."],
    )


class SentimentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: CleanText = Field(
        ..., description="Text to classify for sentiment", examples=["I love this!"]
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank or whitespace only")
        return v


class SentimentResult(BaseModel):
    label: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"] = Field(
        ..., description="Predicted sentiment class", examples=["POSITIVE"]
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence in the predicted label (not a polarity score)",
        examples=[0.9998],
    )


class SentimentResponse(BaseModel):
    text: str = Field(..., description="Original input text", examples=["I love this!"])
    sentiment: SentimentResult = Field(
        ..., description="Classification result with label and score"
    )
    model: str = Field(
        ...,
        description="HuggingFace model used for classification",
        examples=["distilbert-base-uncased-finetuned-sst-2-english"],
    )
    processing_ms: float = Field(
        ..., description="Time spent on inference in milliseconds", examples=[12.34]
    )


class BatchSentimentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texts: list[CleanText] = Field(
        ...,
        min_length=1,
        description="List of texts to classify. Upper bound is set by MAX_BATCH_SIZE.",
        examples=[["I love this!", "Terrible experience."]],
    )


class BatchSentimentItem(BaseModel):
    text: str = Field(..., description="Original input text", examples=["I love this!"])
    sentiment: SentimentResult = Field(..., description="Classification result for this text")


class BatchSentimentResponse(BaseModel):
    results: list[BatchSentimentItem] = Field(
        ..., description="Classification results in input order"
    )
    model: str = Field(
        ...,
        description="HuggingFace model used for classification",
        examples=["distilbert-base-uncased-finetuned-sst-2-english"],
    )
    count: int = Field(..., description="Number of texts in the batch", examples=[3])
    processing_ms: float = Field(
        ..., description="Time spent on batch inference in milliseconds", examples=[45.67]
    )


class ModelInfoResponse(BaseModel):
    model: str = Field(
        ...,
        description="HuggingFace model identifier",
        examples=["distilbert-base-uncased-finetuned-sst-2-english"],
    )
    max_length: int = Field(
        ..., description="Maximum token length accepted by the tokenizer", examples=[512]
    )
    max_batch_size: int = Field(..., description="Maximum texts per batch request", examples=[32])
    version: str = Field(..., description="API package version", examples=["0.1.0"])
    inference_count: int = Field(
        ..., description="Total texts classified by this worker since startup", examples=[1024]
    )
    avg_inference_ms: float = Field(
        ...,
        description="Average inference time per text in milliseconds since startup",
        examples=[8.75],
    )
