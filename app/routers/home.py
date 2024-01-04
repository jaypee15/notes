from fastapi import APIRouter, status
from fastapi.responses import FileResponse

router = APIRouter(prefix="", tags=["home"])


@router.get("/", status_code=status.HTTP_200_OK)
async def home():
    return FileResponse("templates/index.html")