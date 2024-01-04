from fastapi import APIRouter, status

router = APIRouter(prefix="/", tags=["home"])

@router.get("/", status_code=status.HTTP_200_OK)
def home():
    return {"message": "Hello World"}