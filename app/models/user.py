from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Registration Verification
    is_verified: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    registration_otp: Mapped[str] = mapped_column(String(6), nullable=True)
    registration_otp_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Password Reset
    reset_code: Mapped[str] = mapped_column(String(6), nullable=True)
    reset_code_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship to interviews
    interviews: Mapped[list["Interview"]] = relationship(
        "Interview", back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
