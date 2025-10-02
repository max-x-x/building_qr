from sqlalchemy import Column, Integer, DateTime, String, Enum
from sqlalchemy.sql import func
from .database import Base
import enum

class UserRole(str, enum.Enum):
    FOREMAN = "foreman"
    SSK = "ssk"
    IKO = "iko"

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    visit_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(String, nullable=False, index=True)
    user_role = Column(Enum(UserRole), nullable=False, default=UserRole.FOREMAN)
    object_id = Column(Integer, nullable=False, index=True)

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, role={self.user_role}, date={self.visit_date})>"
