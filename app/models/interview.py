from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Index, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import db


class Interview(db.Model):
    __tablename__ = "interviews"
    __table_args__ = (
        Index("idx_user_created_at", "user_id", desc("created_at")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    feedback_level: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    total_questions: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    role_applied_for: Mapped[str] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="interviews")
    responses: Mapped[list["QuestionAnswer"]] = relationship(
        "QuestionAnswer", back_populates="interview", cascade="all, delete-orphan"
    )
    skills: Mapped[list["Skill"]] = relationship(
        "Skill", back_populates="interview", cascade="all, delete-orphan"
    )


class QuestionAnswer(db.Model):
    __tablename__ = "question_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=True) # made nullable for backwards compatibility
    strengths: Mapped[str] = mapped_column(Text, nullable=True) # store as JSON string
    improvements: Mapped[str] = mapped_column(Text, nullable=True) # store as JSON string
    suggestions: Mapped[str] = mapped_column(Text, nullable=True) # store as JSON string

    interview: Mapped["Interview"] = relationship("Interview", back_populates="responses")


class Skill(db.Model):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category_score: Mapped[int] = mapped_column(Integer, nullable=True)
    total_questions_per_category: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    interview: Mapped["Interview"] = relationship("Interview", back_populates="skills")
