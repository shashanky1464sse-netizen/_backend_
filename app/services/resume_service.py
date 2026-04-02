"""
resume_service.py — Section-Aware Resume Parser (spaCy NER + Word2Vec Edition)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Strategy
--------
* No external AI APIs for extraction.
* Three-layer skill extraction:
    Layer 1 — spaCy NER + noun chunks  (structured context matching)
    Layer 2 — Word2Vec similarity       (catches unseen/variant skill names)
    Layer 3 — Comma-split direct match  (handles "Technical: Python, SQL, Git")
* Dynamic section detection via synonym map + flexible header regex.
* Fallback heuristics when no header is found.
* Experience parsing: DATE entities + date-range year difference.
* Questions from tech categories only, capped at MAX_QUESTIONS.

Setup (run once):
    pip install spacy gensim nltk
    python -m spacy download en_core_web_lg
    python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
"""

from __future__ import annotations

import io
import re
import datetime
import threading
from typing import Optional, cast, Any, Dict, List
from difflib import SequenceMatcher

import pdfplumber  # pyre-ignore
import spacy  # pyre-ignore
from spacy.tokens import Doc  # pyre-ignore

import nltk  # pyre-ignore
from nltk.corpus import stopwords  # pyre-ignore
from nltk.tokenize import word_tokenize  # pyre-ignore

from gensim.models import Word2Vec  # pyre-ignore

from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, UnprocessableEntity  # pyre-ignore

# Download required NLTK data silently on first run
for _pkg in ("stopwords", "punkt", "punkt_tab"):
    try:
        nltk.data.find(f"tokenizers/{_pkg}" if "punkt" in _pkg else f"corpora/{_pkg}")
    except LookupError:
        nltk.download(_pkg, quiet=True)

from app.core.logger import get_logger  # pyre-ignore
from app.services import analytics_service  # pyre-ignore
from app.services import llm_service  # pyre-ignore

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Load spaCy model once at module level
# ---------------------------------------------------------------------------
try:
    _NLP = spacy.load("en_core_web_lg")
except OSError:
    try:
        _NLP = spacy.load("en_core_web_sm")
        logger.warning("[ResumeParser] en_core_web_lg not found, falling back to en_core_web_sm. "
                       "Run: python -m spacy download en_core_web_lg for better accuracy.")
    except OSError:
        raise RuntimeError(
            "No spaCy model found. Run: python -m spacy download en_core_web_lg"
        )

# ---------------------------------------------------------------------------
# Word2Vec Skill Similarity Engine
# ---------------------------------------------------------------------------
# The model is trained lazily on first use and cached.
# Corpus = all skill names + their aliases, tokenised into "sentences".
# At extraction time, every resume token is looked up; if its vector is
# within SIMILARITY_THRESHOLD of a known skill vector, it's a match.

_W2V_MODEL: Optional[Word2Vec] = None
_W2V_LOCK  = threading.Lock()
_SIMILARITY_THRESHOLD = 0.72   # tune: lower → more recall, higher → more precision


def _build_w2v_corpus() -> list[list[str]]:
    """
    Build a synthetic training corpus from the skill DB + aliases.
    Each skill becomes a 'sentence' of its own tokens so Word2Vec
    learns the co-occurrence structure of technical terminology.
    """
    stop_words = set(stopwords.words("english"))
    sentences: list[list[str]] = []

    # One sentence per skill (multi-word skills split into tokens)
    all_skills: list[str] = []
    for cat_skills in TECH_SKILLS_DB.values():
        all_skills.extend(cat_skills)
    for aliases in SKILL_ALIASES.values():
        all_skills.extend(aliases)
    all_skills.extend(SOFT_SKILLS_DB)

    for skill in all_skills:
        tokens = [t.lower() for t in word_tokenize(skill)
                  if t.isalpha() and t.lower() not in stop_words]
        if tokens:
            sentences.append(tokens)

    # Add multi-word skills as bigram context sentences
    # e.g. "App Store Connect" → ["app", "store", "connect", "app store", ...]
    for skill in all_skills:
        words = skill.lower().split()
        if len(words) > 1:
            sentences.append(words)

    return sentences


def _get_w2v_model() -> Word2Vec:
    """Return the cached Word2Vec model, training it on first call."""
    global _W2V_MODEL
    if _W2V_MODEL is not None:
        return _W2V_MODEL
    with _W2V_LOCK:
        if _W2V_MODEL is None:
            corpus = _build_w2v_corpus()
            _W2V_MODEL = Word2Vec(
                sentences=corpus,
                vector_size=100,
                window=5,
                min_count=1,      # include all terms even rare ones
                workers=2,
                epochs=50,        # more epochs = better embeddings for small corpus
                sg=1,             # skip-gram works better for rare/technical terms
            )
    return _W2V_MODEL


def _w2v_match_skills(tokens: list[str]) -> set[str]:
    """
    For each token in *tokens*, compute cosine similarity against every
    known skill vector. Returns canonical skill names above threshold.

    This catches:
    - Variant spellings:  "Pytorch" → "PyTorch"
    - Abbreviations:      "ML" → "Machine Learning"  (via alias training)
    - Unseen tech terms:  "SwiftUI" → "Swift" (close vector)
    - Contextual terms:   "recommender" → "Collaborative Filtering"
    """
    model = _get_w2v_model()
    wv    = model.wv
    matched: set[str] = set()

    # Build skill → primary token mapping for similarity lookup
    skill_tokens: dict[str, str] = {}
    for cat_skills in TECH_SKILLS_DB.values():
        for skill in cat_skills:
            primary = skill.lower().split()[0]  # use first token as anchor
            if primary in wv:
                skill_tokens[skill] = primary

    for token in tokens:
        token_lower = token.lower()
        if token_lower not in wv:
            continue
        for skill, anchor in skill_tokens.items():
            try:
                sim = wv.similarity(token_lower, anchor)
                if sim >= _SIMILARITY_THRESHOLD:
                    matched.add(skill)
            except KeyError:
                continue

    return matched


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_QUESTIONS       = 10

# ---------------------------------------------------------------------------
# Section Synonym Map  (unchanged)
# ---------------------------------------------------------------------------
SECTION_SYNONYMS: dict[str, list[str]] = {
    "skills": [
        "skills",
        "skills & strengths",
        "skills and strengths",
        "core competencies",
        "technical skills",
        "technical expertise",
        "professional skills",
        "technical summary",
        "key skills",
        "areas of expertise",
        "competencies",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "career history",
        "work history",
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "key projects",
        "project experience",
    ],
    "education": [
        "education",
        "academic background",
        "qualifications",
        "academic qualifications",
    ],
}

_SYNONYM_TO_SECTION: dict[str, str] = {}
for _section, _synonyms in SECTION_SYNONYMS.items():
    for _syn in _synonyms:
        _SYNONYM_TO_SECTION[_syn.lower().strip()] = _section

# ---------------------------------------------------------------------------
# Categorised Technical Skills Knowledge Base
# ---------------------------------------------------------------------------
TECH_SKILLS_DB: dict[str, list[str]] = {
    "languages": [
        "Python", "Java", "Kotlin", "C++", "C#", "C",
        "Go", "Rust", "Swift", "PHP", "Ruby",
        "JavaScript", "TypeScript", "SQL", "R", "Scala",
        "Bash", "Shell", "MATLAB",
    ],
    "web": [
        "HTML", "CSS", "Tailwind", "Bootstrap",
        "MERN Stack", "MEAN Stack", "LAMP Stack",
        "REST API", "GraphQL", "WebSockets",
    ],
    "backend": [
        "Django", "Flask", "FastAPI", "Spring Boot",
        "Express", "Node.js", "Laravel", "ASP.NET",
        "FastAPI", "Gin", "Echo",
    ],
    "frontend": [
        "React", "Angular", "Vue", "Next.js",
        "Redux", "Tailwind CSS", "Material UI", "Chakra UI",
    ],
    "mobile": [
        # iOS
        "Swift", "SwiftUI", "UIKit", "Xcode", "Core Data",
        "Auto Layout", "Storyboards", "TestFlight",
        "App Store Connect", "WKWebView", "Combine",
        # Android / Cross-platform
        "Android", "Jetpack Compose", "Retrofit",
        "Flutter", "React Native",
    ],
    "database": [
        "MySQL", "PostgreSQL", "MongoDB", "SQLite",
        "Firebase", "Redis", "Oracle", "MSSQL",
        "Cassandra", "DynamoDB", "Supabase",
        "SQL Querying", "Database Management",
    ],
    "devops": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes",
        "CI/CD", "GitHub Actions", "Git", "GitHub",
        "GitLab", "Jenkins", "Terraform", "Linux",
        "Nginx", "Apache",
    ],
    "ai": [
        "Machine Learning", "Deep Learning",
        "TensorFlow", "PyTorch", "Keras",
        "Pandas", "NumPy", "Scikit-learn",
        "Matplotlib", "Seaborn", "Plotly",
        "Data Visualization", "Data Analysis",
        "NLP", "Computer Vision", "LLM",
        "Gemini API", "OpenAI API", "LangChain",
        "Hugging Face", "AIML", "Neural Networks",
        "Collaborative Filtering", "Recommendation Systems",
        "Object Detection", "Image Processing",
    ],
    "architecture": [
        "MVC", "MVVM", "Microservices",
        "System Design", "REST API", "GraphQL",
        "Modular Architecture", "OOP",
        "Object-Oriented Programming",
        "Design Patterns", "SOLID Principles",
    ],
    "testing": [
        "JUnit", "Mockito", "Selenium", "Cypress",
        "Unit Testing", "XCTest", "Pytest",
        "Test-Driven Development", "TDD",
    ],
    "misc": [],
}

SOFT_SKILLS_DB: list[str] = [
    "Communication", "Leadership", "Teamwork",
    "Problem Solving", "Critical Thinking", "Adaptability",
    "Time Management", "Creativity", "Collaboration",
    "Attention to Detail", "Requirement Analysis",
    "Client Communication", "Team Collaboration",
    # Business Analysis skills
    "Requirement Gathering", "Process Mapping",
    "Documentation", "Stakeholder Communication",
    "Analytical Thinking", "Business Analysis",
    "Strategic Planning", "Project Management",
    "Agile", "Scrum",
]

QUESTION_ELIGIBLE_CATEGORIES = {
    "languages", "backend", "frontend", "database", "architecture",
    "mobile", "devops", "ai", "testing",
}

# ---------------------------------------------------------------------------
# Skill Normalisation (Aliases)
# ---------------------------------------------------------------------------
SKILL_ALIASES: dict[str, list[str]] = {
    "React":             ["ReactJS", "React JS", "React-JS"],
    "Node.js":           ["NodeJS", "Node JS", "Node"],
    "PostgreSQL":        ["Postgres", "Postgre SQL"],
    "JavaScript":        ["JS", "Javascript"],
    "TypeScript":        ["TS"],
    "C++":               ["CPP"],
    "REST API":          ["RESTful API", "RESTful APIs", "REST APIs", "RESTful", "REST"],
    "SwiftUI":           ["Swift UI"],
    "UIKit":             ["UI Kit"],
    "App Store Connect": ["AppStore Connect", "App Store"],
    "MERN Stack":        ["MERN"],
    "Machine Learning":  ["ML"],
    "Deep Learning":     ["DL"],
    "Natural Language Processing": ["NLP"],
    "Object-Oriented Programming": ["OOP", "Object Oriented Programming", "Object-Oriented"],
    "CI/CD":             ["CI CD", "Continuous Integration", "Continuous Deployment"],
    "GitHub":            ["Github"],
    "PyTorch":           ["Pytorch"],
    "TensorFlow":        ["Tensorflow", "TF"],
    "Scikit-learn":      ["sklearn", "scikit learn"],
    "Data Visualization": ["Data Viz", "DataViz", "Visualization"],
    "SQL":               ["SQL Querying", "Structured Query Language"],
}

# Flat lookup: alias_lower -> canonical
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in SKILL_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias.lower()] = _canonical


def normalize_skill_aliases(text: str) -> str:
    """Replace alias variants with canonical names before NLP processing."""
    if not _ALIAS_TO_CANONICAL:
        return text
    sorted_aliases = sorted(_ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)
    pattern = r"(?<![a-z0-9_])(" + "|".join(re.escape(a) for a in sorted_aliases) + r")(?![a-z0-9_])"

    def replacer(m: re.Match) -> str:
        return _ALIAS_TO_CANONICAL[m.group(1).lower()]

    return re.sub(pattern, replacer, text, flags=re.IGNORECASE)




# ---------------------------------------------------------------------------
# Role Inference Constants
# ---------------------------------------------------------------------------
ROLE_KEYWORDS = {
    "Backend Engineer":     ["backend", "api", "django", "spring", "fastapi"],
    "Frontend Engineer":    ["react", "angular", "vue", "frontend"],
    "Full Stack Developer": ["frontend", "backend", "mern", "mean"],
    "Data Scientist":       ["machine learning", "data analysis", "pandas", "deep learning", "pytorch", "tensorflow"],
    "iOS Developer":        ["swift", "swiftui", "uikit", "xcode", "ios", "app store"],
    "Mobile Developer":     ["android", "kotlin", "flutter", "react native"],
    "DevOps Engineer":      ["aws", "azure", "docker", "kubernetes", "ci/cd", "devops"],
    "Business Analyst":     ["requirement gathering", "process mapping", "stakeholder", "business analysis", "documentation"],
    "AI/ML Engineer":       ["neural", "pytorch", "tensorflow", "deep learning", "nlp", "computer vision", "recommendation"],
}

ROLE_PRIORITIES = {
    "Backend Engineer":     ["backend", "database", "languages", "architecture", "frontend"],
    "Frontend Engineer":    ["frontend", "languages", "backend", "architecture"],
    "Full Stack Developer": ["backend", "frontend", "languages", "database", "architecture"],
    "Data Scientist":       ["ai", "languages", "database", "architecture"],
    "iOS Developer":        ["mobile", "languages", "architecture", "backend", "database"],
    "Mobile Developer":     ["mobile", "languages", "architecture", "backend"],
    "DevOps Engineer":      ["devops", "architecture", "languages", "database"],
    "Business Analyst":     ["architecture", "languages", "database"],
    "AI/ML Engineer":       ["ai", "languages", "database", "architecture"],
}

# ---------------------------------------------------------------------------
# Pre-compile header detection pattern
# ---------------------------------------------------------------------------
_HEADER_RE = re.compile(r"^\s*([\w][\w\s&,/*-]{0,60}?)\s*:?\s*$")

# ---------------------------------------------------------------------------
# ❶  spaCy NER-based Skill Extraction  (replaces regex matching)
# ---------------------------------------------------------------------------

def _build_skill_lookups() -> tuple[dict, dict, dict]:
    """
    Dynamically build skill lookup dicts from the CURRENT state of TECH_SKILLS_DB
    and SKILL_ALIASES. Called at extraction time so runtime changes take effect
    immediately — no server restart needed.
    """
    all_lower: dict[str, str] = {}
    multi_lower: dict[str, str] = {}
    single_lower: dict[str, str] = {}

    for cat_skills in TECH_SKILLS_DB.values():
        for s in cat_skills:
            sl = s.lower()
            all_lower[sl] = s
            if len(s.split()) > 1:
                multi_lower[sl] = s
            else:
                single_lower[sl] = s

    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            al = alias.lower()
            all_lower[al] = canonical
            if len(alias.split()) > 1:
                multi_lower[al] = canonical
            else:
                single_lower[al] = canonical

    return all_lower, multi_lower, single_lower


def _extract_inline_skill_lines(text: str) -> str:
    """
    Handles lines like:  'Technical: Python, SQL, MERN Stack, Git'
    Strips the label prefix so downstream matchers see plain skill tokens.
    """
    extracted: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^[A-Za-z /\\-]{2,40}:\s*(.+)$", line.strip())
        if match:
            items = match.group(1)
            if "," in items or len(items.split()) <= 5:
                extracted.append(items)
        else:
            extracted.append(line)
    return "\n".join(extracted)


def _extract_skills_spacy(text: str) -> tuple[dict[str, list[str]], list[str]]:
    """
    Three-layer skill extraction:
      Pass 0 — comma-split direct match  (skill lists like "Python, SQL, Git")
      Pass 1 — spaCy noun chunks         (multi-word: "App Store Connect")
      Pass 2 — spaCy token scan          (single-word: Swift, MySQL)
      Pass 3 — sliding window            (multi-word soft skills)
      Pass 4 — NER ORG/PRODUCT entities  (tool names spaCy recognises)
      Pass 5 — Word2Vec similarity       (variants, abbreviations, unseen terms)
    Returns (categorised_tech_dict, soft_skills_list).
    """
    # Build lookups dynamically so any runtime additions to TECH_SKILLS_DB work
    _all_lower, _multi_lower, _single_lower = _build_skill_lookups()

    text = _extract_inline_skill_lines(text)

    matched_tech: set[str] = set()
    matched_soft: set[str] = set()

    # ── Pass 0: comma-split ───────────────────────────────────────────────────
    for line in text.splitlines():
        if "," in line:
            parts = [p.strip().strip("•\u2013-").strip() for p in line.split(",")]
            for part in parts:
                from typing import cast
                pl = part.lower()
                _all_lower_cast = cast(dict, _all_lower)
                _multi_lower_cast = cast(dict, _multi_lower)
                if pl in _all_lower_cast:
                    matched_tech.add(_all_lower_cast[pl])
                elif pl in _multi_lower_cast:
                    matched_tech.add(_multi_lower_cast[pl])
                for soft in SOFT_SKILLS_DB:
                    if soft.lower() == pl:
                        matched_soft.add(soft)

    doc: Doc = _NLP(text)

    # ── Pass 1: noun chunks ───────────────────────────────────────────────────
    for chunk in doc.noun_chunks:
        cl = chunk.text.strip().lower()
        if cl in _multi_lower:
            matched_tech.add(_multi_lower[cl])
            continue
        for skill_lower, canonical in _multi_lower.items():
            if skill_lower in cl or cl in skill_lower:
                matched_tech.add(canonical)

    # ── Pass 2: individual tokens ─────────────────────────────────────────────
    for token in doc:
        tl = token.text.strip().lower()
        if token.is_stop or token.is_punct or len(tl) < 2:
            continue
        if tl in _single_lower:
            matched_tech.add(_single_lower[tl])
        for soft in SOFT_SKILLS_DB:
            if soft.lower() == tl:
                matched_soft.add(soft)

    # ── Pass 3: multi-word soft skills sliding window ─────────────────────────
    from typing import cast
    words = cast(list[str], [t.text for t in doc if not t.is_punct])
    for size in [3, 2]:
        for i in range(len(words) - int(size) + 1):
            phrase = cast(str, " ".join(words[i : i + size])).lower()  # pyre-ignore
            for soft in SOFT_SKILLS_DB:
                if soft.lower() == phrase:
                    matched_soft.add(soft)

    # ── Pass 4: NER ORG/PRODUCT ───────────────────────────────────────────────
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT", "GPE"):
            el = ent.text.strip().lower()
            if el in _all_lower:
                matched_tech.add(_all_lower[el])

    # ── Pass 5: Word2Vec similarity ───────────────────────────────────────────
    stop_words = set(stopwords.words("english"))
    w2v_tokens = [
        t.lower() for t in word_tokenize(text)
        if t.isalpha() and len(t) > 2 and t.lower() not in stop_words
    ]
    try:
        w2v_matches = _w2v_match_skills(w2v_tokens)
        matched_tech.update(w2v_matches)
    except Exception as e:
        logger.warning(f"[W2V] Similarity matching failed: {e}")

    # ── Bucket into categories ────────────────────────────────────────────────
    result: dict[str, list[str]] = {cat: [] for cat in TECH_SKILLS_DB}
    seen: set[str] = set()

    for cat, cat_skills in TECH_SKILLS_DB.items():
        for skill in cat_skills:
            if skill in matched_tech and skill.lower() not in seen:
                seen.add(skill.lower())
                result[cat].append(skill)  # pyre-ignore

    return result, list(matched_soft)


# ---------------------------------------------------------------------------
# ❷  Dynamic Section Detection  (unchanged)
# ---------------------------------------------------------------------------

def detect_sections_dynamic(text: str) -> dict[str, str]:
    lines   = text.splitlines()
    n_lines = len(lines)

    header_positions: list[tuple[int, str]] = []

    for idx, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped or len(stripped) > 80:
            continue
        normalised = re.sub(r"\s+", " ", stripped.rstrip(":").strip()).lower()
        section = _SYNONYM_TO_SECTION.get(normalised)
        if section:
            header_positions.append((idx, section))

    if not header_positions:
        return {"_body": "\n".join(lines)}

    all_bounds = [(-1, "_body")] + header_positions + [(n_lines, "_end")]
    result: dict[str, str] = {}

    for i in range(len(all_bounds) - 1):
        from typing import Any
        start_idx, label = cast(tuple[int, str], all_bounds[i])
        end_idx, _       = cast(tuple[int, str], all_bounds[i + 1])
        content = "\n".join(lines[int(start_idx) + 1 : int(end_idx)]).strip()  # pyre-ignore
        if content:
            result[label] = result.get(label, "") + "\n" + content

    return result


# ---------------------------------------------------------------------------
# ❸  Fallback Heuristic  (unchanged)
# ---------------------------------------------------------------------------

_SKILLS_TRIGGER_WORDS = re.compile(
    r"\b(programming|languages?|software|tools?|technologies|frameworks?|libraries?)\b",
    re.IGNORECASE,
)


def _extract_skills_section_fallback(lines: list[str]) -> str:
    FALLBACK_WINDOW = 15
    collected: list[str] = []
    seen_indices: set[int] = set()

    for idx, line in enumerate(lines):
        if _SKILLS_TRIGGER_WORDS.search(line):
            for offset in range(FALLBACK_WINDOW):
                target = idx + offset
                if target < len(lines) and target not in seen_indices:
                    seen_indices.add(target)
                    collected.append(lines[target])  # pyre-ignore

    return "\n".join(collected)


# ---------------------------------------------------------------------------
# ❹  Experience Detection via spaCy DATE entities + regex fallback
# ---------------------------------------------------------------------------

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_DATE_RANGE_RE = re.compile(
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)?\s*"
    r"(\d{4})\s*[-\u2013\u2014]+\s*"
    r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)?\s*"
    r"(\d{4})|Present|Current|Now|Till\s*date)",
    re.IGNORECASE,
)

_YEARS_EXPLICIT_RE = re.compile(r"(\d+)\s*\+?\s*years?", re.IGNORECASE)


def _strip_education_dates(text: str) -> str:
    """
    Remove lines that belong to the education section so graduation/study
    years don't inflate the work experience calculation.
    """
    edu_markers = re.compile(
        r"\b(bachelor|master|b\.?tech|m\.?tech|b\.?e|m\.?e|phd|"
        r"graduated|graduation|cgpa|gpa|university|college|school|"
        r"expected graduation|pursuing)\b",
        re.IGNORECASE,
    )
    filtered = [line for line in text.splitlines() if not edu_markers.search(line)]
    return "\n".join(filtered)


def _detect_experience_years(text: str) -> Optional[int]:
    """
    Calculate total WORK experience years from the text.

    Priority
    --------
    1. Explicit 'N years' / 'N+ years' statement.
    2. Sum of individual date ranges (handles overlapping jobs correctly).
       Education lines are stripped first to avoid counting study years.
    3. Simple min→max span as last resort.
    """
    current_year = datetime.date.today().year

    # ── Priority 1: explicit statement ───────────────────────────────────────
    explicit = _YEARS_EXPLICIT_RE.findall(text)
    if explicit:
        return min(max(int(m) for m in explicit), 30)

    # Strip education lines before date parsing
    work_text = _strip_education_dates(text)

    # ── Priority 2: sum individual ranges (most accurate) ────────────────────
    ranges: list[tuple[int, int]] = []
    for m in _DATE_RANGE_RE.finditer(work_text):
        try:
            start = int(m.group(1))
            end   = int(m.group(2)) if m.group(2) else current_year
            if 1970 <= start <= current_year and 1970 <= end <= current_year and end >= start:
                ranges.append((start, end))
        except (TypeError, ValueError):
            continue

    if ranges:
        # Merge overlapping ranges to avoid double-counting
        ranges.sort()
        merged: list[tuple[int, int]] = [ranges[0]]
        for s, e in ranges[1:]:  # pyre-ignore
            if s <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        total = sum(e - s for s, e in merged)
        if 0 < total <= 50:
            return total

    # ── Priority 3: spaCy DATE entity span ───────────────────────────────────
    doc: Doc = _NLP(work_text[:4000])  # pyre-ignore
    years_found: list[int] = []
    for ent in doc.ents:
        if ent.label_ == "DATE":
            for yr_match in re.finditer(r"\b(19|20)\d{2}\b", ent.text):
                yr = int(yr_match.group())
                if 1970 <= yr <= current_year:
                    years_found.append(yr)
            if re.search(r"\b(present|current|now)\b", ent.text, re.IGNORECASE):
                years_found.append(current_year)

    if len(years_found) >= 2:
        span = max(years_found) - min(years_found)
        if 0 < span <= 50:
            return span

    return None


# ---------------------------------------------------------------------------
# ❺  Role Extraction via spaCy  (replaces keyword sweep)
# ---------------------------------------------------------------------------

def _extract_roles(full_text: str, technical_skills: dict[str, list[str]]) -> tuple[Optional[str], Optional[str]]:
    """
    Uses spaCy to find job title entities in the top 30% of the resume,
    then maps them to known roles. Falls back to skill-density inference.
    """
    lines = full_text.splitlines()
    search_cutoff = max(int(len(lines) * 0.3), 10)
    top_text = "\n".join(lines[:search_cutoff])  # pyre-ignore

    # Score every role — highest weighted score wins (no early break)
    top_lower  = top_text.lower()
    full_lower = full_text.lower()
    all_skill_strings = [str(s).lower() for cats in technical_skills.values() for s in cats]
    best_role:  Optional[str] = None
    best_score: int = 0

    for role, keywords in ROLE_KEYWORDS.items():
        # Hits in top 30% are weighted 2x — title/summary carry more signal
        top_hits   = sum(2 for kw in keywords if kw in top_lower)
        skill_hits = sum(1 for kw in keywords if kw in all_skill_strings or kw in full_lower)
        score = top_hits + skill_hits
        if score > best_score:
            best_score = score
            best_role  = role

    return None, best_role


# ---------------------------------------------------------------------------
# ❻  Soft Skill extraction from full body (action verbs via POS)
# ---------------------------------------------------------------------------

def _extract_soft_skills_from_body(text: str) -> list[str]:
    """
    Supplement list-based soft skill matching with spaCy POS-based detection.
    Looks for soft skill indicators in verb phrases and noun phrases.
    """
    doc: Doc = _NLP(text[:6000])  # pyre-ignore
    found: set[str] = set()

    # Direct noun chunk match against SOFT_SKILLS_DB
    for chunk in doc.noun_chunks:
        chunk_lower = chunk.text.strip().lower()
        for soft in SOFT_SKILLS_DB:
            if soft.lower() == chunk_lower or soft.lower() in chunk_lower:
                found.add(soft)

    # Token-level match
    for token in doc:
        token_lower = token.text.lower()
        for soft in SOFT_SKILLS_DB:
            if soft.lower() == token_lower:
                found.add(soft)

    return list(found)


# ---------------------------------------------------------------------------
# ❼  Unknown Skills Detection  (spaCy-enhanced)
# ---------------------------------------------------------------------------

def detect_unknown_skills(text: str, known_skills: set[str]) -> list[str]:
    """
    Uses spaCy noun chunks + NER ORG/PRODUCT to surface technology terms
    that look like skills but are absent from TECH_SKILLS_DB.
    """
    doc: Doc = _NLP(text[:8000])  # pyre-ignore
    # Rebuild dynamically so new skills added at runtime are included
    all_lower, _, _ = _build_skill_lookups()
    known_lower = {k.lower() for k in known_skills} | set(all_lower.keys())

    noise_words = {
        "january", "february", "march", "april", "may", "june", "july",
        "august", "september", "october", "november", "december",
        "university", "college", "degree", "bachelor", "master",
        "school", "institute", "academy", "engineering", "science",
        "technology", "management", "application", "developer", "engineer",
        "manager", "project", "product", "system", "software", "hardware",
        "network", "database", "server", "client", "frontend", "backend",
        "fullstack", "agile", "scrum", "company", "inc", "llc", "ltd",
        "corp", "corporation", "technologies", "solutions",
    }

    candidates: set[str] = set()

    # NER entities that look like product/tool names
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT"):
            word = ent.text.strip()
            if (word.lower() not in known_lower
                    and word.lower() not in noise_words
                    and len(word) > 2
                    and re.match(r"[A-Z]", word)):
                candidates.add(word)

    # Capitalised tokens that could be tech terms
    for token in doc:
        word = token.text.strip()
        if (re.match(r"[A-Z][a-zA-Z0-9\.\+\#]{2,}", word)
                and word.lower() not in known_lower
                and word.lower() not in noise_words
                and not token.is_stop):
            candidates.add(word)

    return list(candidates)


# ---------------------------------------------------------------------------
# ❽  Question Generation  (unchanged except role list updated)
# ---------------------------------------------------------------------------

def _generate_questions(
    tech_skills: dict[str, list[str]],
    applied_role: Optional[str] = None,
    weakest_category: Optional[str] = None,
    weak_score: float = 100.0,
    experience: int = 0,
    difficulty: str = "intermediate",
) -> list[dict]:

    if weakest_category and weak_score is not None:
        if weak_score < 40:
            weakness_quota = 5
        elif weak_score < 60:
            weakness_quota = 4
        elif weak_score < 80:
            weakness_quota = 3
        else:
            weakness_quota = 2
    else:
        weakness_quota = 0

    flat_skills = [s for cat, cat_skills in tech_skills.items() for s in cat_skills]
    if flat_skills:
        weak_skills = []
        if weakest_category:
            for cat, skills in tech_skills.items():
                if cat.lower() == weakest_category.lower():
                    weak_skills.extend(skills)

        role_skills = []
        priority_orders = (
            ROLE_PRIORITIES.get(applied_role, list(QUESTION_ELIGIBLE_CATEGORIES))
            if applied_role else list(QUESTION_ELIGIBLE_CATEGORIES)
        )
        # also include misc in priority orders so we don't miss them
        if "misc" not in priority_orders:
            priority_orders.append("misc")
            
        for cat in priority_orders:
            for s in tech_skills.get(cat, []):
                if s not in weak_skills:
                    role_skills.append(s)

        remaining_skills = [s for s in flat_skills if s not in weak_skills and s not in role_skills]

        weak_count     = weakness_quota if weak_skills else 0
        rem            = MAX_QUESTIONS - weak_count
        primary_count  = int(rem * 0.6) if remaining_skills else rem
        secondary_count = rem - primary_count

        question_plan = {
            "weak_skills":     weak_skills,
            "primary_skills":  role_skills,
            "secondary_skills": remaining_skills,
            "distribution": {
                "weak":      weak_count,
                "primary":   primary_count,
                "secondary": secondary_count,
            },
        }

        ai_questions = llm_service.generate_questions(
            question_plan=question_plan,
            role=applied_role or "Software Engineer",
            experience=experience,
            difficulty=difficulty,
            count=MAX_QUESTIONS,
        )
        if ai_questions:
            final_ai: list[dict] = []
            for q in ai_questions:
                main_q     = {"question": q.get("main_question", ""),     "category": q.get("category", ""), "type": "main"}
                follow_up_q = {"question": q.get("follow_up_question", ""), "category": q.get("category", ""), "type": "follow_up"}

                for item in (main_q, follow_up_q):
                    if item["question"] and not any(
                        SequenceMatcher(None, item["question"], ex["question"]).ratio() > 0.85
                        for ex in final_ai
                    ):
                        final_ai.append(item)
                        if len(final_ai) >= MAX_QUESTIONS:
                            break
                if len(final_ai) >= MAX_QUESTIONS:
                    break

            return final_ai

    # ── Static fallback ──────────────────────────────────────────────────────
    questions: list[dict] = []
    lowercase_q_bank = {k.lower(): v for k, v in QUESTION_BANK.items()}

    def is_similar(new_q: str) -> bool:
        if not new_q: return False
        return any(SequenceMatcher(None, str(new_q), str(ex["question"])).ratio() > 0.85 for ex in questions)

    def add_pair(q_pair: dict, skill: str) -> None:
        for key, qtype in (("main", "main"), ("follow_up", "follow_up")):
            if len(questions) < MAX_QUESTIONS and not is_similar(q_pair[key]):
                questions.append({"question": q_pair[key], "category": skill, "type": qtype})

    adaptive_quota_pairs = max(1, int(weakness_quota) // 2) if (
        weakest_category
        and str(weakest_category).lower() in [str(k).lower() for k in QUESTION_ELIGIBLE_CATEGORIES]
    ) else 0

    weakest_cat_exact = None
    if adaptive_quota_pairs > 0 and weakest_category:
        for cat in tech_skills:
            if str(cat).lower() == str(weakest_category).lower() and tech_skills.get(cat):
                weakest_cat_exact = cat
                break

    base_categories = list(QUESTION_ELIGIBLE_CATEGORIES)
    if applied_role and applied_role in ROLE_PRIORITIES:
        ordered = [p for p in ROLE_PRIORITIES[applied_role] if p in base_categories]
        remaining = [c for c in base_categories if c not in ordered]
        categories_to_query = ordered + remaining
    else:
        categories_to_query = base_categories

    if weakest_cat_exact:
        for skill in tech_skills.get(weakest_cat_exact, []):
            if adaptive_quota_pairs <= 0 or len(questions) >= MAX_QUESTIONS:  # pyre-ignore
                break
            q_list = lowercase_q_bank.get(skill.lower(), [{
                "main":     f"Describe your experience with {skill} in a production environment.",
                "follow_up": f"What are the most challenging aspects of working with {skill}?",
            }])
            for q_pair in q_list:
                adaptive_quota_int: int = int(adaptive_quota_pairs)
                if adaptive_quota_int <= 0:
                    break
                add_pair(q_pair, skill)
                adaptive_quota_pairs = int(adaptive_quota_pairs) - 1  # pyre-ignore

    for category in categories_to_query:
        if len(questions) >= MAX_QUESTIONS:
            break
        for skill in tech_skills.get(category, []):
            if len(questions) >= MAX_QUESTIONS:
                break
            q_list = lowercase_q_bank.get(skill.lower(), [{  # pyre-ignore
                "main":     f"Can you walk me through a complex problem you solved using {skill}?",
                "follow_up": f"How do you stay updated with the latest developments in {skill}?",
            }])
            for q_pair in q_list:
                if len(questions) >= MAX_QUESTIONS:
                    break
                add_pair(q_pair, skill)

    if len(questions) < MAX_QUESTIONS:
        all_skills = [s for cat, cs in tech_skills.items() if cat != "misc" for s in cs]
        for skill in all_skills:
            if len(questions) >= MAX_QUESTIONS:
                break
            if sum(1 for q in questions if q["category"] == skill) >= 2:
                continue
            q_list = lowercase_q_bank.get(skill.lower(), [{  # pyre-ignore
                "main":     f"How would you explain the core concepts of {skill} to a junior engineer?",
                "follow_up": f"Describe a time you had to optimise performance related to {skill}.",
            }])
            for q_pair in q_list:
                if len(questions) >= MAX_QUESTIONS:
                    break
                add_pair(q_pair, skill)

    return questions


# ---------------------------------------------------------------------------
# ❾  File Validation & PDF Extraction  (unchanged)
# ---------------------------------------------------------------------------

def _validate_file(file, raw: bytes) -> None:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise BadRequest(description="Only PDF files are accepted.")
    if len(raw) > MAX_FILE_SIZE_BYTES:
        raise RequestEntityTooLarge(description="File exceeds the 5 MB size limit.")


def _extract_text(raw: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages)
    except Exception as exc:
        raise UnprocessableEntity(description=f"Could not parse PDF: {exc}")


# ---------------------------------------------------------------------------
# ❿  Public Service Function
# ---------------------------------------------------------------------------

def process_resume(file, user_id: int) -> dict:
    """
    Full pipeline:
      validate → extract text → detect sections → spaCy NER skill extraction
      → experience detection → role extraction → question generation.
    """
    raw: bytes = file.read()
    _validate_file(file, raw)

    full_text = _extract_text(raw)
    full_text = normalize_skill_aliases(full_text)
    lines     = full_text.splitlines()

    # ── Step 1: Dynamic section detection ────────────────────────────────────
    sections = detect_sections_dynamic(full_text)

    # ── Step 2: Resolve best corpus for skill matching ────────────────────────
    skills_section_text: str = sections.get("skills", "")

    if not skills_section_text.strip():
        skills_section_text = _extract_skills_section_fallback(lines)
        if not skills_section_text.strip():
            skills_section_text = full_text

    # ── Step 3: spaCy NER skill extraction ───────────────────────────────────
    # Use skills section + projects section for broader context
    projects_text  = sections.get("projects", "")
    experience_text = sections.get("experience", "")
    enriched_text  = "\n".join(filter(None, [skills_section_text, projects_text, experience_text]))

    tech_skills_raw, soft_skills = _extract_skills_spacy(enriched_text)

    # Also pick up soft skills mentioned outside the skills section
    soft_skills_body = _extract_soft_skills_from_body(full_text)
    all_soft = list(dict.fromkeys(soft_skills + soft_skills_body))


    # ── Step 4: AI-Powered Extraction (Experience & Role) ─────────────────────
    # We call Gemini to get more accurate years and role target.
    # Keep heuristics as robust fallbacks.
    ai_details = llm_service.extract_resume_details(full_text)
    ai_exp = ai_details.get("experience_years")
    ai_role = ai_details.get("target_role")

    # ── Step 5: Experience detection (Heuristic Fallback) ─────────────────────
    experience_section_text = sections.get("experience", full_text)
    h_experience = _detect_experience_years(experience_section_text)
    if h_experience is None:
        full_text_fallback = full_text
        if "education" in sections:
            full_text_fallback = full_text_fallback.replace(sections["education"], "")
        h_experience = _detect_experience_years(full_text_fallback)
    
    # Use AI experience if explicitly detected (including 0 for fresh grads), otherwise fallback to heuristic
    experience = ai_exp if ai_exp is not None else (h_experience or 0)

    # ── Step 6: Role extraction (Heuristic Fallback) ─────────────────────────
    technical_skills = {
        "languages":    tech_skills_raw.get("languages",    []),
        "backend":      tech_skills_raw.get("backend",      []),
        "frontend":     tech_skills_raw.get("frontend",     []),
        "mobile":       tech_skills_raw.get("mobile",       []),
        "database":     tech_skills_raw.get("database",     []),
        "devops":       tech_skills_raw.get("devops",       []),
        "ai":           tech_skills_raw.get("ai",           []),
        "architecture": tech_skills_raw.get("architecture", []),
        "testing":      tech_skills_raw.get("testing",      []),
    }

    _, h_inferred_target_role = _extract_roles(full_text, technical_skills)
    
    # Use AI role if found, otherwise fallback to heuristic
    inferred_target_role = ai_role if ai_role else h_inferred_target_role
    fallback_role = inferred_target_role

    # ── Step 6: Analytics + question generation ───────────────────────────────
    analytics_data   = analytics_service.get_category_performance_data(user_id)
    weakest_category = analytics_data.get("weakest_category")
    weak_score       = 100.0
    if weakest_category and "category_scores" in analytics_data:
        scores = [c["score"] for c in analytics_data["category_scores"] if c["category"] == weakest_category]
        if scores:
            weak_score = scores[0]

    questions = _generate_questions(
        tech_skills_raw,
        applied_role=fallback_role,
        weakest_category=weakest_category,
        weak_score=weak_score,
        experience=experience,
    )

    # ── Step 7: tools_frameworks ──────────────────────────────────────────────
    tools_set: list[str] = []
    seen_tools: set[str] = set()
    for cat in ("web", "devops", "testing"):
        for skill in tech_skills_raw.get(cat, []):
            if skill.lower() not in seen_tools:
                seen_tools.add(skill.lower())
                tools_set.append(skill)

    # ── Step 8: Unknown skills detection ─────────────────────────────────────
    all_known: set[str] = set()
    for cs in TECH_SKILLS_DB.values():
        all_known.update(cs)
    for aliases in SKILL_ALIASES.values():
        all_known.update(aliases)

    unknown_skills = detect_unknown_skills(full_text, all_known)

    # ── Step 9: AI Fallback Classification of Unknown Skills ─────────────────
    # Any candidate that survived all 6 NLP passes gets a final AI review.
    # The AI classifies them into technical / tools / soft (or discards noise).
    # Results are merged into the primary buckets so clients need no changes.
    ai_classified: dict[str, list[str]] = {}
    if unknown_skills:
        try:
            ai_classified = llm_service.ai_classify_unknown_skills(
                candidates=unknown_skills[:20],
                resume_snippet=full_text[:500],
            )
            # Merge technical_skills → languages bucket (catches langs like Rust, CUDA, etc.)
            ai_tech = ai_classified.get("technical_skills", [])
            existing_tech_lower = {s.lower() for sl in technical_skills.values() for s in sl}
            for skill in ai_tech:
                if skill.lower() not in existing_tech_lower:
                    technical_skills.setdefault("languages", []).append(skill)
                    existing_tech_lower.add(skill.lower())

            # Merge tools_frameworks → tools_set
            tools_lower = {s.lower() for s in tools_set}
            for skill in ai_classified.get("tools_frameworks", []):
                if skill.lower() not in tools_lower:
                    tools_set.append(skill)
                    tools_lower.add(skill.lower())

            # Merge soft_skills → all_soft
            soft_lower = {s.lower() for s in all_soft}
            for skill in ai_classified.get("soft_skills", []):
                if skill.lower() not in soft_lower:
                    all_soft.append(skill)
                    soft_lower.add(skill.lower())

            logger.info(
                f"[AI Classify] Added {len(ai_tech)} tech, "
                f"{len(ai_classified.get('tools_frameworks', []))} tools, "
                f"{len(ai_classified.get('soft_skills', []))} soft skills via AI fallback."
            )
        except Exception as _ai_err:
            logger.warning(f"[AI Classify] Step 9 failed non-fatally: {_ai_err}")

    # Build a human-readable summary for the endpoint response
    total_tech = sum(len(v) for v in technical_skills.values())

    if experience >= 6:
        experience_level = "Expert"
    elif experience >= 3:
        experience_level = "Intermediate"
    else:
        experience_level = "Beginner"

    return {
        "technical_skills":          technical_skills,
        "tools_frameworks":          tools_set,
        "soft_skills":               all_soft,
        "unknown_skills":            unknown_skills,
        "ai_classified_skills":      ai_classified,   # NEW: what Layer 7 identified
        "detected_experience_years": int(experience),
        "experience_level":          experience_level,
        "inferred_target_role":      inferred_target_role or "Not detected",
        "applied_role":              inferred_target_role or "Not detected",
        "generated_questions":       questions,
        "extraction_summary": {
            "total_technical_skills": int(total_tech),
            "total_soft_skills":      len(all_soft),
            "experience_years":       int(experience),
            "experience_level":       experience_level,
            "inferred_target_role":   inferred_target_role or "Not detected",
        },
    }


# ---------------------------------------------------------------------------
# Utility: bucket_skills & generate_questions_from_preferences  (unchanged)
# ---------------------------------------------------------------------------

def bucket_skills(skills: list[str]) -> dict[str, list[str]]:
    technical_skills: dict[str, list[str]] = {cat: [] for cat in TECH_SKILLS_DB}
    technical_skills["misc"] = []
    for skill in skills:
        found_cat = None
        for cat, kw_list in TECH_SKILLS_DB.items():
            if any(s.lower() == skill.lower() for s in kw_list):
                found_cat = cat
                break
        if found_cat:
            technical_skills[found_cat].append(skill)  # pyre-ignore
        else:
            technical_skills["misc"].append(skill)  # pyre-ignore
    return technical_skills


def generate_questions_from_preferences(
    skills: list[str],
    role: Optional[str] = None,
    experience: int = 0,
    difficulty: str = "intermediate",
    user_id: Optional[int] = None,
) -> list[dict]:
    if not skills:
        return []

    technical_skills = bucket_skills(skills)
    weakest_category = None

    if user_id is not None:
        try:
            analytics_data   = analytics_service.get_category_performance_data(user_id)
            weakest_category = analytics_data.get("weakest_category")
        except Exception as e:
            logger.warning(f"[generate_questions_from_preferences] analytics failed: {e}")

    return _generate_questions(
        tech_skills=technical_skills,
        applied_role=role,
        weakest_category=weakest_category,
        experience=experience,
        difficulty=difficulty,
    )

def generate_single_question_replacement(
    current_question: str,
    skills: list[str],
    role: Optional[str] = None,
    experience: int = 0,
    difficulty: str = "intermediate"
) -> dict:
    """
    Calls llm_service to generate exactly one new question replacing current_question.
    Transforms it to match the standard UI format.
    """
    from app.services import llm_service
    raw_q = llm_service.generate_single_question(
        current_question=current_question,
        role=role or "Software Engineer",
        experience=experience,
        difficulty=difficulty,
        skills=skills
    )
    
    cat = raw_q.get("category", "General")
    mq = raw_q.get("main_question", "")
    
    return {
        "question": mq,
        "category": cat,
        "type": "main"  # the UI maps this just as a single string question block
    }


QUESTION_BANK: dict[str, list[dict[str, str]]] = {
    "Python":      [{"main": "Explain your experience with Python and describe the projects you built with it.",
                     "follow_up": "Which Python frameworks or libraries have you used, and what were your reasons for choosing them?"}],
    "Java":        [{"main": "Describe a Java project you worked on and the design patterns you applied.",
                     "follow_up": "How do you manage memory and performance in a Java application?"}],
    "Kotlin":      [{"main": "What advantages does Kotlin offer over Java for Android development?",
                     "follow_up": "Describe how you use Kotlin coroutines for asynchronous programming."}],
    "C++":         [{"main": "Explain memory management in C++ and how you avoid common pitfalls.",
                     "follow_up": "How do you handle multi-threading safely in C++?"}],
    "C#":          [{"main": "Describe your experience with the .NET ecosystem using C#.",
                     "follow_up": "How do you apply SOLID principles in a C# project?"}],
    "C":           [{"main": "Explain pointer arithmetic and how it differs from higher-level languages.",
                     "follow_up": "How do you manage dynamic memory allocation in C?"}],
    "Go":          [{"main": "What makes Go well-suited for concurrent systems?",
                     "follow_up": "Describe a service you built using Go and the challenges you faced."}],
    "Rust":        [{"main": "Explain Rust's ownership model and how it prevents memory errors.",
                     "follow_up": "When would you choose Rust over C++ for a systems project?"}],
    "Swift":       [{"main": "How does Swift's optional system improve safety compared to Objective-C?",
                     "follow_up": "Describe your experience building an iOS application with Swift."}],
    "SwiftUI":     [{"main": "How does SwiftUI's declarative syntax differ from UIKit's imperative approach?",
                     "follow_up": "Describe how you managed state across views in a SwiftUI application."}],
    "UIKit":       [{"main": "Walk me through the UIViewController lifecycle and when you use each method.",
                     "follow_up": "How do you handle Auto Layout constraints programmatically vs in Interface Builder?"}],
    "PHP":         [{"main": "How do you structure a scalable PHP application?",
                     "follow_up": "Explain how you secure a PHP application against SQL injection and XSS."}],
    "Ruby":        [{"main": "What makes Ruby on Rails productive for web development?",
                     "follow_up": "How do you test a Ruby application effectively?"}],
    "JavaScript":  [{"main": "Explain the event loop and how asynchronous JavaScript works.",
                     "follow_up": "How do you manage state in a large JavaScript application?"}],
    "TypeScript":  [{"main": "How does TypeScript's type system improve large codebase maintainability?",
                     "follow_up": "Describe a scenario where strict TypeScript types caught a runtime bug early."}],
    "Django":      [{"main": "How would you design a REST API using Django REST Framework?",
                     "follow_up": "How does Django's ORM differ from raw SQL queries?"}],
    "Flask":       [{"main": "Describe the architecture of a Flask application you built.",
                     "follow_up": "How do you handle authentication and authorisation in Flask?"}],
    "FastAPI":     [{"main": "How does FastAPI's dependency injection system work?",
                     "follow_up": "Why would you choose FastAPI over Flask for a new project?"}],
    "Spring Boot": [{"main": "Explain how Spring Boot auto-configuration works.",
                     "follow_up": "How do you secure a Spring Boot REST API?"}],
    "Express":     [{"main": "How do you structure middleware in an Express application?",
                     "follow_up": "Describe how you handle errors globally in Express."}],
    "Node.js":     [{"main": "How does Node.js handle concurrency without multiple threads?",
                     "follow_up": "When should you use Node.js over a multi-threaded server?"}],
    "Laravel":     [{"main": "Describe the request lifecycle in a Laravel application.",
                     "follow_up": "How do you use Eloquent ORM to handle complex relationships?"}],
    "ASP.NET":     [{"main": "How does ASP.NET Core's middleware pipeline work?",
                     "follow_up": "Explain how dependency injection is configured in ASP.NET Core."}],
    "React":       [{"main": "Explain the virtual DOM and how React's reconciliation works.",
                     "follow_up": "How do you manage global state in a React application?"}],
    "Angular":     [{"main": "Describe Angular's component lifecycle hooks and when you use them.",
                     "follow_up": "How does Angular's dependency injection differ from other frameworks?"}],
    "Vue":         [{"main": "How does Vue's reactivity system work?",
                     "follow_up": "Describe how you would structure a large-scale Vue application."}],
    "Next.js":     [{"main": "Explain the difference between SSR and SSG in Next.js.",
                     "follow_up": "How does Next.js improve SEO for a React application?"}],
    "MySQL":       [{"main": "Can you walk me through optimising a slow MySQL query?",
                     "follow_up": "Explain the difference between INNER JOIN, LEFT JOIN, and RIGHT JOIN."}],
    "PostgreSQL":  [{"main": "What PostgreSQL-specific features have you used and why?",
                     "follow_up": "How do you handle database migrations in a production PostgreSQL system?"}],
    "MongoDB":     [{"main": "When would you choose MongoDB over a relational database?",
                     "follow_up": "How do you model relationships in MongoDB?"}],
    "SQLite":      [{"main": "What are the limitations of SQLite for production systems?",
                     "follow_up": "How did you use SQLite in a mobile or embedded project?"}],
    "Firebase":    [{"main": "Describe how you have used Firestore for real-time data synchronisation.",
                     "follow_up": "How do you handle Firebase security rules effectively?"}],
    "Redis":       [{"main": "What use cases make Redis the right choice over a relational DB?",
                     "follow_up": "How would you use Redis for session management or caching?"}],
    "System Design":  [{"main": "How would you design a scalable REST API to serve millions of users?",
                        "follow_up": "Describe the trade-offs between SQL and NoSQL databases at scale."}],
    "Microservices":  [{"main": "How do microservices communicate with each other reliably?",
                        "follow_up": "What challenges have you faced managing distributed data in microservices?"}],
    "REST API":       [{"main": "What principles make a REST API truly RESTful?",
                        "follow_up": "How do you version and document a public REST API?"}],
    "GraphQL":        [{"main": "What problems does GraphQL solve that REST cannot?",
                        "follow_up": "How do you prevent over-fetching and under-fetching in a GraphQL schema?"}],
    "MVC":            [{"main": "Explain the MVC design pattern and how you applied it in a mobile app.",
                        "follow_up": "What are the limitations of MVC compared to MVVM?"}],
    "MVVM":           [{"main": "How does the MVVM pattern improve testability in iOS applications?",
                        "follow_up": "Describe how data binding works in your MVVM implementation."}],
    "App Store Connect": [{"main": "Walk me through the App Store submission process you follow.",
                           "follow_up": "How do you handle app rejection feedback from Apple review?"}],
    "TestFlight":     [{"main": "How do you use TestFlight to manage beta testing distribution?",
                        "follow_up": "How do you collect and act on feedback from TestFlight testers?"}],
}