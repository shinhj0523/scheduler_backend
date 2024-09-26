from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal, engine, Base
from models import User, Reservation
from sqlalchemy.orm import Session
from schemas import ReservationCreate, ReservationOut, UserOut, UserCreate
from api import authenticate_user, create_reservation, create_user
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용 (보안을 위해 배포 시에는 특정 출처만 허용 권장)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],  # 모든 헤더 허용
)

# 새로운 Lifespan 이벤트 핸들러 사용
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

# 비동기 데이터베이스 세션 의존성 설정
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 학번이 10자리 숫자인지 검사하는 유틸리티 함수
def validate_student_id(student_id: str):
    if not (student_id.isdigit() and len(student_id) == 10):
        raise HTTPException(status_code=400, detail="학번은 10자리 숫자여야 합니다.")

# 사용자 인증 엔드포인트 추가
@app.post("/users/authenticate", response_model=UserOut)
async def authenticate_user_endpoint(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 비동기 호출 시 await 추가
    db_user = await authenticate_user(db, user.name, user.student_id)
    if not db_user:
        raise HTTPException(status_code=400, detail="Authentication failed")
    return db_user

    
# 예약하기
@app.post("/users/{user_id}/reservations", response_model=ReservationOut)
async def create_reservation(user_id: int, reservation: ReservationCreate, db: AsyncSession = Depends(get_db)):
    try:
        # 입력받은 예약 시간 문자열을 datetime 객체로 변환
        try:
            reserved_time = datetime.strptime(reservation.reserved_time, "%Y-%m-%d %H:%M:%S")
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}. Use YYYY-MM-DD HH:MM:SS")
        
        # 해당 시간대에 이미 예약이 있는지 확인
        existing_reservations = await db.execute(
            select(Reservation).filter_by(reserved_time=reserved_time)
        )
        if existing_reservations.first():
            raise HTTPException(status_code=400, detail="Time slot already reserved")

        # 예약 생성
        new_reservation = Reservation(
            user_id=user_id,
            reserved_time=reserved_time,
            duration_hours=reservation.duration_hours
        )
        db.add(new_reservation)
        await db.commit()
        await db.refresh(new_reservation)

        return new_reservation

    except Exception as e:
        # 예외 발생 시 500 에러와 함께 발생한 예외 메시지를 반환
        raise HTTPException(status_code=500, detail=str(e))


# 회원가입 엔드포인트
@app.post("/users/register", response_model=UserOut)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await create_user(db, user)
    return db_user

@app.get("/reservations/{date}")
async def get_reservations(date: str, db: AsyncSession = Depends(get_db)):
    try:
        # 날짜만 전달된 경우 시간 "00:00:00"을 추가
        if len(date) == 10:
            date += " 00:00:00"
        query_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")

    # 예약된 시간과 유저 이름, 유저 ID를 함께 조회
    result = await db.execute(
        select(Reservation, User).join(User).filter(
            Reservation.reserved_time.between(query_date, query_date.replace(hour=23, minute=59))
        )
    )
    reservations = result.fetchall()

    # 예약된 시간, 유저 이름, 유저 ID를 반환
    return {
        "reservations": [
            {
                "hour": r.Reservation.reserved_time.hour,
                "user_name": r.User.name,
                "user_id": r.User.id,  # 유저 ID도 함께 반환
                "id": r.Reservation.id  # 예약 ID도 반환
            } 
            for r in reservations
        ]
    }


@app.put("/reservations/{reservation_id}")
async def update_reservation(reservation_id: int, new_time: str, db: AsyncSession = Depends(get_db)):
    try:
        # 새로운 시간 문자열을 datetime 객체로 변환
        new_reserved_time = datetime.strptime(new_time, "%Y-%m-%d %H:%M:%S")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}. Use YYYY-MM-DD HH:MM:SS")

    # 기존 예약 찾기
    result = await db.execute(select(Reservation).filter_by(id=reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # 새 시간에 이미 예약이 있는지 확인
    existing_reservations = await db.execute(
        select(Reservation).filter_by(reserved_time=new_reserved_time)
    )
    if existing_reservations.first():
        raise HTTPException(status_code=400, detail="Time slot already reserved")

    # 예약 시간 수정
    reservation.reserved_time = new_reserved_time
    await db.commit()
    return {"status": "Reservation updated", "new_time": new_reserved_time}

@app.delete("/reservations/{reservation_id}")
async def delete_reservation(reservation_id: int, db: AsyncSession = Depends(get_db)):
    # 예약 찾기
    result = await db.execute(select(Reservation).filter_by(id=reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # 예약 삭제
    await db.delete(reservation)
    await db.commit()

    return {"status": "Reservation deleted"}
