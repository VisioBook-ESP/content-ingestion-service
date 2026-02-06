from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def validate():
    return {"status": "ok"}
