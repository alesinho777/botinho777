"""Esquemas pydantic del JSON que el motor entrega al bot/LLM (ver seccion 11.7 del spec)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["baja", "media", "alta"]


class Market1x2(BaseModel):
    H: float
    D: float
    A: float


class MarketBtts(BaseModel):
    yes: float
    no: float


class OverUnderLine(BaseModel):
    over: float
    under: float


class MarketOu(BaseModel):
    line_1_5: OverUnderLine = Field(alias="1.5")
    line_2_5: OverUnderLine = Field(alias="2.5")
    line_3_5: OverUnderLine = Field(alias="3.5")

    model_config = {"populate_by_name": True}


class CorrectScore(BaseModel):
    score: str
    p: float


class Markets(BaseModel):
    x1x2: Market1x2 = Field(alias="1x2")
    btts: MarketBtts
    ou: MarketOu
    cs_top: list[CorrectScore]

    model_config = {"populate_by_name": True}


class Prediction(BaseModel):
    fixture_id: str
    kickoff: str
    competition_id: str
    home: str
    away: str
    lambda_home: float
    lambda_away: float
    markets: Markets
    factors: list[str]
    confidence: Confidence
    model: str
    trained_until: str
