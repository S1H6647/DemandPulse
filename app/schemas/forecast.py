from datetime import date

from pydantic import BaseModel, Field


# Request
class ForecastRequest(BaseModel):
    date: date
    store_nbr: int = Field(gt=0)
    family: str = Field(min_length=1)
    onpromotion: int = Field(ge=0)


# Response
class ForecastResponse(BaseModel):
    date: date
    store_nbr: int
    family: str
    predicted_sales: float
