from fastapi import APIRouter

router = APIRouter()

@router.post("/report")
def report():
    return {"message": "Report endpoint - to be implemented"}
