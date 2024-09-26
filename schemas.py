# Pydantic 스키마 파일입니다. 데이터 유효성 검사와 API 요청 및 응답 구조를 정의합니다.
from datetime import datetime
from pydantic import BaseModel, Field, constr
from typing import List


# 사용자 기본 정보 스키마 (이름과 학번)
class UserBase(BaseModel):
    name: str
    student_id: str  # 학번은 단순 문자열로 처리

class UserCreate(BaseModel):
    name: str
    student_id: str  # 학번은 단순 문자열로 처리

# API 응답에 사용할 사용자 출력 스키마
class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True

# 예약 기본 정보 스키마
class ReservationBase(BaseModel):
    reserved_time: str  # 예약 시간
    duration_hours: int  # 예약 시간 길이 (최대 2시간)

# 예약 생성 스키마
class ReservationCreate(BaseModel):
    reserved_time: str  # 예약 시간을 문자열로 받음
    duration_hours: int

class ReservationOut(BaseModel):
    id: int
    user_id: int
    reserved_time: datetime  # 여기서는 여전히 datetime을 유지
    duration_hours: int

    class Config:
        # Pydantic이 datetime을 자동으로 변환하도록 설정
        json_encoders = {
            datetime: lambda v: v.isoformat(),  # datetime을 ISO 형식의 문자열로 변환
        }
        from_attributes = True