import enum

from sqlalchemy import Column, Integer, DateTime, String, Enum, Float
from sqlalchemy.sql import func

from .database import Base

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
    area_id = Column(Integer, nullable=True, index=True)
    area_name = Column(String, nullable=True)

    def __repr__(self):
        return (f"<Session(id={self.id}, user_id={self.user_id}, "
                f"role={self.user_role}, date={self.visit_date})>")

class SessionHistory(Base):
    __tablename__ = "session_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    object_id = Column(Integer, nullable=False, index=True)
    sub_polygon_id = Column(Integer, nullable=True, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    def __repr__(self):
        return (f"<SessionHistory(id={self.id}, user_id={self.user_id}, "
                f"object_id={self.object_id}, date={self.date})>")
