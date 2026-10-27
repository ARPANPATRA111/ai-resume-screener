"""Score how well a resume matches a job description.

The final score (0-100) is a weighted mix of three signals:

* skill match      - share of the job's skills that appear in the resume
* text similarity  - TF-IDF cosine similarity between the two documents
* experience       - resume years of experience vs. the years the job asks for
"""

import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.skills import extract_skills

WEIGHTS = {"skills": 0.5, "similarity": 0.35, "experience": 0.15}

# TF-IDF similarity between two related documents rarely goes above ~0.5,
# so it is rescaled to make the number meaningful on a 0-100 scale.
SIMILARITY_CEILING = 0.5

YEARS_PATTERN = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


@dataclass
class ScreeningResult:
    filename: str
    candidate: str
    email: str | None
    score: float
    verdict: str
    breakdown: dict[str, float]
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    extra_skills: list[str] = field(default_factory=list)
    years_experience: int = 0


def text_similarity(job_text: str, resume_text: str) -> float:
    """Cosine similarity of the TF-IDF vectors of both texts (0.0 - 1.0)."""
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        vectors = vectorizer.fit_transform([job_text, resume_text])
    except ValueError:  # empty vocabulary, e.g. a blank or image-only PDF
        return 0.0
    return float(cosine_similarity(vectors[0], vectors[1])[0][0])


def extract_years(text: str) -> int:
    """Largest 'N years' / 'N+ yrs' value mentioned in the text, or 0."""
    years = [int(value) for value in YEARS_PATTERN.findall(text)]
    return max((y for y in years if y <= 40), default=0)


def guess_candidate_name(text: str, filename: str) -> str:
    """Use the first short line of the resume as the name, else the file name."""
    for line in text.splitlines()[:5]:
        line = line.strip()
        words = line.split()
        if 1 < len(words) <= 4 and all(word.replace(".", "").isalpha() for word in words):
            return line.title()
    return filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()


def get_verdict(score: float) -> str:
    if score >= 70:
        return "Strong Match"
    if score >= 40:
        return "Potential Match"
    return "Weak Match"


def screen_resume(job_text: str, resume_text: str, filename: str) -> ScreeningResult:
    job_skills = extract_skills(job_text)
    resume_skills = extract_skills(resume_text)
    matched = job_skills & resume_skills

    skill_score = len(matched) / len(job_skills) if job_skills else 0.0
    similarity_score = min(text_similarity(job_text, resume_text) / SIMILARITY_CEILING, 1.0)

    required_years = extract_years(job_text)
    candidate_years = extract_years(resume_text)
    if required_years == 0:
        experience_score = 1.0
    else:
        experience_score = min(candidate_years / required_years, 1.0)

    breakdown = {
        "skills": round(skill_score * 100, 1),
        "similarity": round(similarity_score * 100, 1),
        "experience": round(experience_score * 100, 1),
    }
    score = round(sum(breakdown[key] * weight for key, weight in WEIGHTS.items()), 1)

    email = EMAIL_PATTERN.search(resume_text)

    return ScreeningResult(
        filename=filename,
        candidate=guess_candidate_name(resume_text, filename),
        email=email.group() if email else None,
        score=score,
        verdict=get_verdict(score),
        breakdown=breakdown,
        matched_skills=sorted(matched),
        missing_skills=sorted(job_skills - resume_skills),
        extra_skills=sorted(resume_skills - job_skills),
        years_experience=candidate_years,
    )


def rank_resumes(job_text: str, resumes: dict[str, str]) -> list[ScreeningResult]:
    """Screen every resume ({filename: text}) and return them best first."""
    results = [screen_resume(job_text, text, name) for name, text in resumes.items()]
    return sorted(results, key=lambda result: result.score, reverse=True)
