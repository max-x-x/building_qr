from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, date
from ..templates import LoginRequest
from ..database import get_db
from ..models import Session as SessionModel
from ..api import APIClient

router = APIRouter()

class LoginResponse(BaseModel):
    status: str
    access: bool
    token: str | None = None
    message: str

@router.post("/login", response_model=LoginResponse)
async def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    
    api_client = APIClient()
    api_response = api_client.login(login_data.email, login_data.password)

    if not api_response or api_response.get("status") == "error" or not api_response.get("access"):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    user_id = api_response.get("user_id")
    token = api_response.get("token")

    from datetime import datetime, timedelta
    start = datetime.combine(date.today(), datetime.min.time())
    end = start + timedelta(days=1)

    has_today = db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.visit_date >= start,
        SessionModel.visit_date < end
    ).first() is not None

    if has_today:
        return LoginResponse(status="success", access=True, token=token, message="Вход выполнен успешно")
    else:
        return LoginResponse(status="success", access=False, token=token, message="Доступ запрещен - нет записи на сегодня")
