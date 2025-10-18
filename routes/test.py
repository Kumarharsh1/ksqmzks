from fastapi import APIRouter

router = APIRouter()

@router.get("/api/test")
async def test_backend():
    return {"status": "Backend is alive", "message": "Test endpoint working"}