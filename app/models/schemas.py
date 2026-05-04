from pydantic import BaseModel, Field


class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, examples=["I love this!"])


class SentimentResult(BaseModel):
    label: str = Field(..., examples=["POSITIVE"])
    score: float = Field(..., ge=0.0, le=1.0, examples=[0.9998])


class SentimentResponse(BaseModel):
    text: str
    sentiment: SentimentResult
    model: str
