# SQLAlchemy 모델 정의 파일입니다.
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# 사용자 테이블을 위한 SQLAlchemy 모델입니다.
class User(Base):
    __tablename__ = "users"
    
    # 고유 ID
    id = Column(Integer, primary_key=True, index=True)
    # 사용자 이름
    name = Column(String(100), nullable=False)
    # 학번 (10자리 숫자, 고유)
    student_id = Column(String(10), unique=True, nullable=False)
    
    # 사용자의 예약 관계 설정
    reservations = relationship("Reservation", back_populates="user")

# 예약 테이블을 위한 SQLAlchemy 모델입니다.
class Reservation(Base):
    __tablename__ = "reservations"
    
    # 고유 ID
    id = Column(Integer, primary_key=True, index=True)
    # 사용자 ID (외래 키)
    user_id = Column(Integer, ForeignKey("users.id"))
    # 예약 시간
    reserved_time = Column(DateTime, nullable=False)
    # 예약 시간 길이 (최대 2시간)
    duration_hours = Column(Integer, nullable=False)
    
    # 사용자와의 관계 설정
    user = relationship("User", back_populates="reservations")
