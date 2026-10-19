from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Student
from app.schemas import StudentCreate, StudentOut, StudentUpdate
from app.timeutil import utc_now

router = APIRouter(prefix="/students", tags=["students"])


def get_active_student(db: Session, student_id: int) -> Student:
    """Yo'q yoki soft-delete qilingan o'quvchi → 404."""
    student = db.get(Student, student_id)
    if student is None or student.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "O'quvchi topilmadi")
    return student


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(data: StudentCreate, db: Session = Depends(get_db)) -> Student:
    student = Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("", response_model=list[StudentOut])
def list_students(group: str | None = None, db: Session = Depends(get_db)) -> list[Student]:
    query = select(Student).where(Student.deleted_at.is_(None)).order_by(Student.id)
    if group is not None:
        query = query.where(Student.group == group.strip())
    return list(db.scalars(query))


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)) -> Student:
    return get_active_student(db, student_id)


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)) -> Student:
    student = get_active_student(db, student_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)) -> Response:
    student = get_active_student(db, student_id)
    student.deleted_at = utc_now()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
