# 데이터베이스 CRUD 작업을 처리하는 파일입니다.
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import User, Reservation
from fastapi import HTTPException
from schemas import ReservationCreate, UserCreate
from sqlalchemy.ext.asyncio import AsyncSession

# 사용자 인증 함수
def authenticate_user(db: Session, name: str, student_id: str):
    # 이름과 학번이 일치하는 사용자를 데이터베이스에서 검색합니다.
    user = db.query(User).filter(User.name == name, User.student_id == student_id).first()
    
    # 사용자가 없을 경우 에러를 반환합니다.
    if not user:
        raise HTTPException(status_code=400, detail="잘못된 사용자 정보입니다.")
    
    return user

# 새로운 예약을 생성하는 함수 (비동기 처리)
async def create_reservation(db: AsyncSession, user_id: int, reservation: ReservationCreate):
    # 예약 정보를 데이터베이스에 추가 (비동기 처리)
    db_reservation = Reservation(
        user_id=user_id,
        reserved_time=reservation.reserved_time,
        duration_hours=reservation.duration_hours
    )
    db.add(db_reservation)
    await db.commit()  # 비동기 커밋
    await db.refresh(db_reservation)  # 비동기 리프레시

    return db_reservation

# 사용자 등록 함수 (비동기 처리)
async def create_user(db: AsyncSession, user: UserCreate):
    # 이미 동일한 학번이 존재하는지 확인 (비동기 쿼리)
    result = await db.execute(
        select(User).filter(User.student_id == user.student_id)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 학번입니다.")
    
    # 새로운 사용자 생성
    db_user = User(name=user.name, student_id=user.student_id)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user



# 사용자 인증 함수 (비동기 처리)
async def authenticate_user(db: AsyncSession, name: str, student_id: str):
    # 비동기 쿼리 실행
    result = await db.execute(
        select(User).filter(User.name == name, User.student_id == student_id)
    )
    user = result.scalar_one_or_none()

    # 사용자가 없을 경우 에러 반환
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    return user
