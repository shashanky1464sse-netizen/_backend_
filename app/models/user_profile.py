from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import db

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    full_name: Mapped[str] = mapped_column(String(120), nullable=True)
    job_title: Mapped[str] = mapped_column(String(120), nullable=True)
    location: Mapped[str] = mapped_column(String(120), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    profile_photo_url: Mapped[str] = mapped_column(String(255), nullable=True)

    skills_json: Mapped[str] = mapped_column(Text, nullable=True)
    previous_role: Mapped[str] = mapped_column(String(100), nullable=True)
    target_role: Mapped[str] = mapped_column(String(100), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=True)
    experience_level: Mapped[str] = mapped_column(String(50), nullable=True)
    preferred_difficulty: Mapped[str] = mapped_column(String(20), nullable=True, default="beginner")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
