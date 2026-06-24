from fastapi import APIRouter

router = APIRouter()


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}
