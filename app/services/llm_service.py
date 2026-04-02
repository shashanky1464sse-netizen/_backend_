

import json
import logging
import time
from typing import cast, Any

from openai import OpenAI, RateLimitError, AuthenticationError, APIError

from app.core.config import get_settings  # pyre-ignore

logger = logging.getLogger(__name__)
settings = get_settings()


NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"


GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"


CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
CEREBRAS_MODEL = "llama3.1-70b"

# Request timeouts (connect_timeout, read_timeout) in seconds
# Without these, a slow/hung provider blocks the entire fallback chain
_CONNECT_TIMEOUT = 10.0   # time to establish TCP connection
_READ_TIMEOUT    = 45.0   # time to wait for the full streaming response
import httpx
_HTTP_CLIENT = httpx.Client(timeout=httpx.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT))

def _get_nvidia_client(api_key: str) -> OpenAI:
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key, http_client=_HTTP_CLIENT, max_retries=0)

# ── Core request helpers ───────────────────────────────────────────────────────

def _nvidia_chat(prompt: str, max_tokens: int = 1024) -> str:
    
    keys = settings.nvidia_api_keys
    if not keys:
        raise RuntimeError("No NVIDIA_API_KEYS configured")

    last_error: Exception = RuntimeError("No keys tried")
    for idx, key in enumerate(keys):
        try:
            client = _get_nvidia_client(key)
            resp = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            text = (resp.choices[0].message.content or "").strip()
            logger.debug(f"NVIDIA key #{idx + 1} succeeded.")
            return text
        except (RateLimitError, AuthenticationError) as e:
            logger.warning(f"NVIDIA key #{idx + 1} failed ({type(e).__name__}). Trying next…")
            last_error = e
        except APIError as e:
            logger.warning(f"NVIDIA API error with key #{idx + 1}: {e}. Trying next…")
            last_error = e
        except Exception as e:
            logger.warning(f"Unexpected error with NVIDIA key #{idx + 1}: {e}. Trying next…")
            last_error = e

    raise last_error


def _get_cerebras_client() -> OpenAI:
    if not settings.cerebras_api_key:
        raise RuntimeError("CEREBRAS_API_KEY not set")
    return OpenAI(base_url=CEREBRAS_BASE_URL, api_key=settings.cerebras_api_key, http_client=_HTTP_CLIENT, max_retries=0)


def _get_groq_client() -> OpenAI:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    return OpenAI(base_url=GROQ_BASE_URL, api_key=settings.groq_api_key, http_client=_HTTP_CLIENT, max_retries=0)


def _get_openrouter_client() -> OpenAI:
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=settings.openrouter_api_key, http_client=_HTTP_CLIENT, max_retries=0)


def _cerebras_chat(prompt: str, max_tokens: int = 1024) -> str:
    client = _get_cerebras_client()
    resp = client.chat.completions.create(
        model=CEREBRAS_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    text = (resp.choices[0].message.content or "").strip()
    logger.debug("Cerebras key succeeded.")
    return text


def _groq_chat(prompt: str, max_tokens: int = 1024) -> str:
    client = _get_groq_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    text = (resp.choices[0].message.content or "").strip()
    logger.debug("Groq key succeeded.")
    return text


def _openrouter_chat(prompt: str, max_tokens: int = 1024) -> str:
    client = _get_openrouter_client()
    referer = settings.origins_list[0] if settings.origins_list else "http://localhost"
    resp = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
        extra_headers={
            "HTTP-Referer": referer,
            "X-Title": settings.app_name,
        }
    )
    text = (resp.choices[0].message.content or "").strip()
    logger.debug("OpenRouter key succeeded.")
    return text


def _call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """
    Unified entry point: NVIDIA NIM → Cerebras → OpenRouter → Groq → raises RuntimeError.
    """
    # 1. Try NVIDIA
    if settings.nvidia_api_keys:
        try:
            return _nvidia_chat(prompt, max_tokens=max_tokens)
        except Exception as e:
            logger.error(f"All NVIDIA keys failed: {e}. Falling back to Cerebras.")

    # 2. Try Cerebras
    if settings.cerebras_api_key:
        try:
            return _cerebras_chat(prompt, max_tokens=max_tokens)
        except Exception as e:
            logger.error(f"Cerebras failed: {e}. Falling back to OpenRouter.")

    # 3. Try OpenRouter
    if settings.openrouter_api_key:
        try:
            return _openrouter_chat(prompt, max_tokens=max_tokens)
        except Exception as e:
            logger.error(f"OpenRouter failed: {e}. Falling back to Groq.")

    # 4. Try Groq
    if settings.groq_api_key:
        try:
            return _groq_chat(prompt, max_tokens=max_tokens)
        except Exception as e:
            logger.error(f"Groq failed: {e}.")

    raise RuntimeError("No LLM provider available (no configured keys worked).")

# ── JSON helpers ───────────────────────────────────────────────────────────────

def _clean_json(text: str) -> str:
    """Strip markdown fences from LLM JSON responses."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]  # pyre-ignore
    elif text.startswith("```"):
        text = text[3:]  # pyre-ignore
    if text.endswith("```"):
        text = text[:-3]  # pyre-ignore
    return text.strip()


# ── Public API ─────────────────────────────────────────────────────────────────

def evaluate_answer(question: str, answer: str, category: str, role: str | None = None) -> dict:
    """
    Evaluates an interview answer using NVIDIA NIM → OpenRouter → Groq → deterministic fallback.
    """
    fallback_response = {
        "score": min(100, max(0, len(answer) // 2)),
        "strengths": [
            f"Addressed the core concept of the {category} question.",
            "Provided a structured response."
        ],
        "improvements": [
            "Consider adding more real-world examples.",
            "Expand on edge cases related to the topic."
        ],
        "suggestions": [
            "Review further documentation to improve confidence."
        ]
    }

    if not settings.nvidia_api_keys and not settings.cerebras_api_key and not settings.openrouter_api_key and not settings.groq_api_key:
        logger.warning("No LLM provider available. Using fallback scoring.")
        return fallback_response

    role_context = (
        f" The candidate is interviewing for a '{role}' position. "
        f"Vary the strictness of suggestions against standard industry expectations for this role."
    ) if role else " Provide general technical feedback."

    prompt = (
        f"You are an expert technical interviewer evaluating a candidate's answer.\n"
        f"Evaluate the following answer to the given question in category '{category}'.{role_context}\n"
        f"Provide a score from 0–100, a list of strengths, a list of improvements, "
        f"and a list of actionable suggestions tailored to their role.\n"
        f"Return ONLY a valid JSON object — NO markdown, NO extra text:\n"
        f'{{"score": integer, "strengths": ["string"], "improvements": ["string"], "suggestions": ["string"]}}\n\n'
        f"Question: {question}\n\nCandidate Answer: {answer}"
    )

    try:
        raw = _call_llm(prompt, max_tokens=512)
        result = cast(dict[str, Any], json.loads(_clean_json(raw)))
        return {
            "score": max(0, min(100, int(result.get("score", 0)))),
            "strengths": result.get("strengths", []) or ["Good effort."],
            "improvements": result.get("improvements", []) or ["Detail edge cases."],
            "suggestions": result.get("suggestions", []) or ["Practice more."]
        }
    except Exception as e:
        logger.error(f"LLM evaluation failed: {e}")
        return fallback_response


def generate_questions(question_plan: dict, role: str, experience: int, difficulty: str, count: int) -> list:
    """
    Generates tailored interview questions.
    Returns an empty list on complete failure so callers can use static fallbacks.
    """
    dist = question_plan.get("distribution", {})
    weak_count = max(1, dist.get("weak", 0) // 2) if dist.get("weak", 0) > 0 else 0
    primary_count = max(1, dist.get("primary", 0) // 2) if dist.get("primary", 0) > 0 else 0
    secondary_count = max(0, 5 - weak_count - primary_count)
    pair_count = max(1, count // 2)

    weak_skills = ", ".join(question_plan.get("weak_skills", [])) or "None"
    primary_skills = ", ".join(question_plan.get("primary_skills", [])) or "None"
    secondary_skills = ", ".join(question_plan.get("secondary_skills", [])) or "None"

    prompt = (
        f"Generate a realistic technical interview with exactly {pair_count} main technical questions.\n\n"
        f"Distribution:\n"
        f"  Weak skills        → {weak_count} questions\n"
        f"  Primary role skills → {primary_count} questions\n"
        f"  Secondary skills   → {secondary_count} questions\n\n"
        f"Skills:\n"
        f"  Weak:      {weak_skills}\n"
        f"  Primary:   {primary_skills}\n"
        f"  Secondary: {secondary_skills}\n\n"
        f"Experience: {experience} years\n"
        f"Difficulty: The candidate requested {difficulty.upper()} level questions. Ensure questions challenge the candidate strictly according to this difficulty.\n\n"
        f"Rules:\n"
        f"- Exactly {pair_count} main technical questions\n"
        f"- Each must have one follow-up question probing deeper\n"
        f"- Match the candidate's experience level\n"
        f"- Prioritize weak skills first; avoid duplicates\n"
        f"- The 'category' field MUST be the EXACT specific technical skill being tested (e.g. 'Python', 'React', 'System Design'), NOT a generic group string like 'Primary skills'.\n"
        f"- Return ONLY a valid JSON array, no markdown:\n"
        f'[{{"main_question": "...", "follow_up_question": "...", "category": "..."}}]'
    )

    try:
        raw = _call_llm(prompt, max_tokens=1024)
        result = cast(Any, json.loads(_clean_json(raw)))
        limit = int(count)
        if isinstance(result, list):
            return [q for i, q in enumerate(result) if i < limit]
        elif isinstance(result, dict) and "questions" in result:
            return [q for i, q in enumerate(cast(list, result["questions"])) if i < limit]
        return []
    except Exception as e:
        logger.error(f"LLM question generation failed: {e}")
        return []

def generate_single_question(current_question: str, role: str, experience: int, difficulty: str, skills: list[str]) -> dict:
    """
    Generates exactly 1 new replacement technical interview question.
    It MUST be completely different from the current question.
    """
    skills_str = ", ".join(skills) if skills else "General technical skills"
    
    prompt = (
        f"You are a technical interviewer hiring for: {role}\n"
        f"The candidate has {experience} years of experience. They requested {difficulty.upper()} difficulty.\n"
        f"Their skills: {skills_str}\n\n"
        f"They want to skip this current question:\n"
        f"\"{current_question}\"\n\n"
        f"Generate EXACTLY ONE new, different technical question.\n"
        f"It must have one main question and one follow-up question probing deeper.\n"
        f"The 'category' field MUST be the specific technical skill being tested.\n"
        f"Return ONLY a valid JSON object (NOT an array), no markdown:\n"
        f'{{"main_question": "...", "follow_up_question": "...", "category": "..."}}'
    )

    try:
        raw = _call_llm(prompt, max_tokens=512)
        result = cast(dict, json.loads(_clean_json(raw)))
        return result
    except Exception as e:
        logger.error(f"LLM single question generation failed: {e}")
        return {
            "main_question": "Can you describe a challenging technical problem you solved recently?",
            "follow_up_question": "What specific approach did you take, and what was the outcome?",
            "category": skills[0] if skills else "General"
        }



def generate_interview_summary(role: str, overall_score: int, feedback_level: str, category_scores: dict) -> str:
    """
    Synthesizes a 5–6 line professional summary of the interview.
    Falls back to a short deterministic string on failure.
    """
    fallback_summary = (
        f"Interview completed. Score: {overall_score}/100 — {feedback_level}. "
        f"Topics covered: {', '.join(category_scores.keys()) if category_scores else 'general topics'}."
    )

    role_str = f"'{role}' role" if role else "Software Engineering position"
    cats = ", ".join([f"{k} (Score: {v})" for k, v in category_scores.items()])

    prompt = (
        f"You are an expert technical interviewer synthesizing a final candidate report.\n"
        f"The candidate just finished an interview for a {role_str}.\n"
        f"Overall Score: {overall_score}/100 ({feedback_level}).\n"
        f"Category Breakdown: {cats}.\n\n"
        f"Write a professional summary paragraph of their performance in MAXIMUM 50 WORDS. "
        f"Briefly highlight their strength and weakness relating it to the {role_str}.\n"
        f"Return ONLY the summary paragraph text — NO markdown, NO bullet points, NO JSON."
    )

    try:
        return _call_llm(prompt, max_tokens=300).replace("\n", " ").strip()
    except Exception as e:
        logger.error(f"LLM summary generation failed: {e}")
        return fallback_summary


def ai_classify_unknown_skills(candidates: list, resume_snippet: str = "") -> dict:
    """
    Layer 7 (AI fallback): classify unknown candidate terms into one of the three
    user-facing skill categories.

    Parameters
    ----------
    candidates     : list of strings detected by detect_unknown_skills() but not
                     matched by the DB-backed passes.
    resume_snippet : first ~500 chars of resume text for context.

    Returns
    -------
    dict with keys: "technical_skills", "tools_frameworks", "soft_skills"
    Each value is a list[str].  Returns an empty dict on any failure so it is
    always safe to call — it must never break the pipeline.
    """
    if not candidates:
        return {}

    empty: dict = {"technical_skills": [], "tools_frameworks": [], "soft_skills": []}

    if not settings.nvidia_api_keys and not settings.cerebras_api_key and not settings.openrouter_api_key and not settings.groq_api_key:
        logger.warning("[AI Classify] No LLM provider available — skipping fallback classification.")
        return empty

    candidate_str = ", ".join(str(c) for c in candidates[:20])

    prompt = (
        "You are an expert resume parser. Classify each of the following skill candidates "
        "into exactly one of four buckets based on the context of the resume snippet below.\n\n"
        "Bucket definitions:\n"
        "  technical_skills  - Core programming languages, CS concepts, algorithms, paradigms, "
        "AI/ML frameworks (e.g. Rust, OOP, CUDA, Transformers)\n"
        "  tools_frameworks  - Specific tools, libraries, platforms, cloud services, DevOps, "
        "web frameworks, mobile SDKs (e.g. Langflow, BentoML, Streamlit, Chainlit, Expo)\n"
        "  soft_skills       - Interpersonal or business skills (e.g. Negotiation, Mentoring)\n"
        "  none              - Not a skill, noise, proper noun, company name, etc.\n\n"
        f"Resume context (first 500 chars):\n{resume_snippet[:500]}\n\n"
        f"Skill candidates to classify: {candidate_str}\n\n"
        "Return ONLY a valid JSON object — no markdown, no explanation:\n"
        '{"technical_skills": ["..."], "tools_frameworks": ["..."], "soft_skills": ["..."], "none": ["..."]}'
    )

    try:
        raw = _call_llm(prompt, max_tokens=512)
        result = cast(dict, json.loads(_clean_json(raw)))
        return {
            "technical_skills": [str(s) for s in result.get("technical_skills", [])],
            "tools_frameworks": [str(s) for s in result.get("tools_frameworks", [])],
            "soft_skills":      [str(s) for s in result.get("soft_skills", [])],
        }
    except Exception as e:
        logger.warning(f"[AI Classify] Fallback skill classification failed: {e}")
        return empty


def extract_resume_details(text: str) -> dict:
    """
    Extracts experience years and target role from resume text via NVIDIA NIM → OpenRouter → Groq.
    Returns an empty dict on failure.
    """
    prompt = (
        "You are an expert HR recruiter extracting structured data from a resume.\n"
        "Your job: extract ONLY professional/work experience years and the most suitable job role.\n\n"
        "RULES (follow strictly):\n"
        "1. Count ONLY paid work experience: full-time jobs, part-time jobs, freelance gigs.\n"
        "2. DO NOT count any of these as experience:\n"
        "   - School / High School / Secondary School / Junior College\n"
        "   - Bachelor's / Master's / PhD / Engineering degrees / any college education\n"
        "   - Internships, traineeships, apprenticeships\n"
        "   - Certifications, courses, bootcamps\n"
        "   - Any entry under sections named 'Education' or 'Certifications'\n"
        "3. IF YOU SEE A SECTION NAMED 'EDUCATION', COMPLETELY IGNORE ALL DATES IN THAT SECTION.\n"
        "4. If the resume has NO paid work experience at all (e.g., a fresh graduate), return 0.\n"
        "5. For target_role: infer the most relevant job title from their skills and any work experience.\n\n"
        "Return ONLY valid JSON, no markdown, no explanation:\n"
        '{"experience_years": integer, "target_role": "string or null"}\n\n'
        f"Resume Text:\n{str(text)[0:8000]}"
    )

    try:
        raw = _call_llm(prompt, max_tokens=256)
        result = cast(dict[str, Any], json.loads(_clean_json(raw)))
        return {
            "experience_years": int(result.get("experience_years", 0)) if result.get("experience_years") is not None else 0,
            "target_role": result.get("target_role")
        }
    except Exception as e:
        logger.error(f"LLM resume extraction failed: {e}")
        return {}

def validate_job_role(role: str) -> bool:
    """
    Asks the LLM if the provided string is a valid professional job role.
    Returns True if valid, False if it's random gibberish or not a job.
    """
    if not role or len(role.strip()) < 2:
        return False
        
    prompt = (
        f"You are a validation expert for an HR system.\n"
        f"Is the following string a reasonably valid professional job title or role? "
        f"It doesn't have to be perfect, just not random gibberish or inappropriate.\n"
        f"Role to check: \"{role}\"\n\n"
        f"Reply ONLY with 'true' or 'false', nothing else."
    )
    
    try:
        raw = _call_llm(prompt, max_tokens=10).strip().lower()
        return "true" in raw
    except Exception as e:
        logger.warning(f"LLM validate_job_role failed: {e}")
        # Fail open if LLM is down
        return True

def validate_skills(skills: list[str]) -> bool:
    """
    Asks the LLM if ALL provided strings are valid professional skills.
    Returns True if ALL are valid, False if ANY are random gibberish.
    """
    if not skills:
        return True
        
    skills_str = ", ".join(skills)
    prompt = (
        f"You are a validation expert for an HR system.\n"
        f"Are ALL of the following strings reasonably valid professional skills or tools? "
        f"They don't have to be perfect, just not random gibberish, nonsense, or highly inappropriate.\n"
        f"Skills to check: [{skills_str}]\n\n"
        f"Reply ONLY with 'true' if ALL are valid, or 'false' if ANY are invalid gibberish/nonsense."
    )
    
    try:
        raw = _call_llm(prompt, max_tokens=10).strip().lower()
        return "true" in raw
    except Exception as e:
        logger.warning(f"LLM validate_skills failed: {e}")
        # Fail open if LLM is down
        return True

