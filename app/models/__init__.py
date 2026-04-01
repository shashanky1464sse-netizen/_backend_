# Models package — import all ORM models here so Base.metadata knows about them
# before database.init_db() calls create_all().

from app.models.interview import Interview, QuestionAnswer, Skill  # noqa: F401
from app.models.user import User  # noqa: F401

__all_models__ = [User, Interview, QuestionAnswer, Skill]
