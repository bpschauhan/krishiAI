from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.weather import (
    CurrentWeatherResponse,
    DailyForecastResponse,
    HourlyForecastResponse,
    WeatherHistoryResponse,
    WeatherQuery,
)
from app.services.weather_service import WeatherService, weather_service

router = APIRouter(prefix="/weather")


def get_weather_service() -> WeatherService:
    return weather_service


@router.get("/current", response_model=CurrentWeatherResponse)
def get_current_weather(
    farm_id: int | None = Query(default=None, gt=0),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    db: Session = Depends(get_db),
    service: WeatherService = Depends(get_weather_service),
) -> CurrentWeatherResponse:
    return _handle_weather_call(service.current_weather, db, farm_id, longitude, latitude)


@router.get("/hourly", response_model=HourlyForecastResponse)
def get_hourly_forecast(
    farm_id: int | None = Query(default=None, gt=0),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
    service: WeatherService = Depends(get_weather_service),
) -> HourlyForecastResponse:
    query = _build_query(farm_id, longitude, latitude)
    try:
        return service.hourly_forecast(db, query, hours=hours)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/daily", response_model=DailyForecastResponse)
def get_daily_forecast(
    farm_id: int | None = Query(default=None, gt=0),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    days: int = Query(default=7, ge=1, le=16),
    db: Session = Depends(get_db),
    service: WeatherService = Depends(get_weather_service),
) -> DailyForecastResponse:
    query = _build_query(farm_id, longitude, latitude)
    try:
        return service.daily_forecast(db, query, days=days)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/history", response_model=WeatherHistoryResponse)
def get_weather_history(
    farm_id: int | None = Query(default=None, gt=0),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    service: WeatherService = Depends(get_weather_service),
) -> WeatherHistoryResponse:
    query = _build_query(farm_id, longitude, latitude)
    try:
        return service.historical_weather(db, query, start_date=start_date, end_date=end_date)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


def _handle_weather_call(
    handler,
    db: Session,
    farm_id: int | None,
    longitude: float | None,
    latitude: float | None,
):
    query = _build_query(farm_id, longitude, latitude)
    try:
        return handler(db, query)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _build_query(farm_id: int | None, longitude: float | None, latitude: float | None) -> WeatherQuery:
    try:
        return WeatherQuery(farm_id=farm_id, longitude=longitude, latitude=latitude)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc
