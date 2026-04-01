import json
from collections import defaultdict
from app.database import db
from app.models.interview import Interview, QuestionAnswer, Skill
from app.services import llm_service
from sqlalchemy.orm import joinedload


def _feedback_level(score: int) -> str:
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Average"
    return "Needs Improvement"


def _build_summary(score: int, level: str, categories: list[str]) -> str:
    cats = ", ".join(categories) if categories else "general topics"
    return (
        f"Interview completed. Score: {score}/100 — {level}. "
        f"Topics covered: {cats}."
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def create_interview(interview_data: dict, user_id: int) -> Interview:
    """
    Score the interview using ai_service, determine feedback level, persist the interview,
    all question-answer pairs with granular AI feedback, and aggregated category scores.

    Answers are evaluated CONCURRENTLY to cut wall-clock time from ~N*45 s → ~45 s.
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    responses = interview_data.get('responses', [])
    role_applied_for = interview_data.get('role_applied_for')

    def evaluate_one(r: dict) -> dict:
        """Evaluate a single Q&A pair — runs in a thread pool."""
        question = r.get('question', '')
        answer   = r.get('answer', '')
        category = r.get('category', '').strip()
        try:
            ai_eval = llm_service.evaluate_answer(question, answer, category, role_applied_for)
        except Exception:
            length_val = min(100, len(answer) // 2)
            ai_eval = {
                "score":        length_val,
                "strengths":    ["Length-based fallback scoring applied."],
                "improvements": ["Answer length could be longer for a better fallback score."],
                "suggestions":  ["Include more technical depth."]
            }
        return {
            'question': question,
            'answer':   answer,
            'category': category,
            'ai_eval':  ai_eval,
        }

    # ── Evaluate all answers CONCURRENTLY ───────────────────────────────────
    # Using min(len, 5) workers — avoids spawning 10 threads that all hit the
    # same rate-limited API simultaneously; 4-5 is the sweet spot.
    max_workers = min(len(responses), 5) if responses else 1
    evaluated_responses: list[dict] = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(evaluate_one, r): r for r in responses}
        for future in futures:
            try:
                evaluated_responses.append(future.result(timeout=60))
            except FuturesTimeout:
                r = futures[future]
                length_val = min(100, len(r.get('answer', '')) // 2)
                evaluated_responses.append({
                    'question': r.get('question', ''),
                    'answer':   r.get('answer', ''),
                    'category': r.get('category', '').strip(),
                    'ai_eval': {
                        "score":        length_val,
                        "strengths":    ["Evaluation timed out — length-based score used."],
                        "improvements": ["Provide more detailed answers for AI evaluation."],
                        "suggestions":  ["Try again with a stable network connection."]
                    }
                })
            except Exception as exc:
                r = futures[future]
                evaluated_responses.append({
                    'question': r.get('question', ''),
                    'answer':   r.get('answer', ''),
                    'category': r.get('category', '').strip(),
                    'ai_eval': {
                        "score":        0,
                        "strengths":    [],
                        "improvements": [f"Evaluation failed: {exc}"],
                        "suggestions":  []
                    }
                })

    # ── Aggregate category scores ────────────────────────────────────────────
    category_score_sums = defaultdict(int)
    category_counts     = defaultdict(int)
    for r in evaluated_responses:
        category = r['category']
        if category:
            category_score_sums[category] += r['ai_eval']['score']
            category_counts[category]     += 1
    category_scores = {}
    for cat, total in category_score_sums.items():
        category_scores[cat] = int(total / category_counts[cat])

    # Overall score is the average of category averages, or 0 if empty
    overall_score = 0
    if category_scores:
        overall_score = int(sum(category_scores.values()) / len(category_scores))

    level = _feedback_level(overall_score)
    # Synthesize the 3-4 line contextual AI summary covering all categories
    summary = llm_service.generate_interview_summary(
        role=role_applied_for,
        overall_score=overall_score,
        feedback_level=level,
        category_scores=category_scores
    )

    # Persist Interview
    interview = Interview(
        user_id=user_id,
        feedback_level=level,
        score=overall_score,
        summary=summary,
        total_questions=len(evaluated_responses),
        role_applied_for=role_applied_for
    )
    db.session.add(interview)
    db.session.flush()  # get interview.id without committing

    # Persist QuestionAnswer rows with structured AI Feedback
    for r in evaluated_responses:
        db.session.add(QuestionAnswer(
            interview_id=interview.id,
            question=r['question'],
            answer=r['answer'],
            category=r['category'],
            score=r['ai_eval']['score'],
            strengths=json.dumps(r['ai_eval']['strengths']),
            improvements=json.dumps(r['ai_eval']['improvements']),
            suggestions=json.dumps(r['ai_eval'].get('suggestions', []))
        ))

    # Persist Skill rows (one per unique category with aggregated score)
    for cat, c_score in category_scores.items():
        db.session.add(Skill(
            interview_id=interview.id, 
            skill_name=cat,
            category_score=c_score,
            total_questions_per_category=category_counts[cat]
        ))

    db.session.commit()
    db.session.refresh(interview)
    return interview


def get_all_interviews(user_id: int) -> list[Interview]:
    """Return all interviews for user, newest first. Eagerly loads skills to avoid N+1 queries."""
    return (
        db.session.query(Interview)
        .filter(Interview.user_id == user_id)
        .options(joinedload(Interview.skills))
        .order_by(Interview.created_at.desc())
        .all()
    )


def get_interview_by_id(interview_id: int, user_id: int) -> Interview | None:
    """Fetch a single interview with all Q&A and skills eagerly loaded."""
    return (
        db.session.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == user_id)
        .options(joinedload(Interview.responses), joinedload(Interview.skills))
        .first()
    )
