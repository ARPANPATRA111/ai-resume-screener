from app.scorer import extract_years, get_verdict, rank_resumes, screen_resume
from app.skills import extract_skills

JOB = """We need a machine learning engineer with 2+ years of experience.
Must know Python, PyTorch, Docker and SQL."""


def test_extract_skills_handles_aliases_and_symbols():
    skills = extract_skills("Worked with sklearn, C++ and ci/cd pipelines in Python")
    assert {"scikit-learn", "C++", "CI/CD", "Python"} <= skills


def test_extract_skills_ignores_partial_words():
    assert "Java" not in extract_skills("Built apps in JavaScript")
    assert "Machine Learning" not in extract_skills("Wrote clean HTML pages")


def test_extract_years():
    assert extract_years("I have 3+ years of experience and 1 yr of teaching") == 3
    assert extract_years("no numbers here") == 0


def test_verdict_thresholds():
    assert get_verdict(80) == "Strong Match"
    assert get_verdict(60) == "Potential Match"
    assert get_verdict(20) == "Weak Match"


def test_good_resume_scores_higher_than_unrelated_one():
    good = "Jane Doe\nMachine learning engineer, 3 years of experience with Python, PyTorch, Docker and SQL."
    bad = "John Roe\nGraphic designer with 5 years of experience in Photoshop and branding."

    ranked = rank_resumes(JOB, {"bad.txt": bad, "good.txt": good})

    assert ranked[0].filename == "good.txt"
    assert ranked[0].score > ranked[1].score
    assert ranked[1].verdict == "Weak Match"


def test_screen_resume_reports_missing_skills():
    result = screen_resume(JOB, "Alex Kim\nPython developer, 2 years", "alex.txt")

    assert result.candidate == "Alex Kim"
    assert "Python" in result.matched_skills
    assert "PyTorch" in result.missing_skills
    assert result.breakdown["experience"] == 100.0


def test_empty_resume_does_not_crash():
    result = screen_resume(JOB, "", "empty.txt")
    assert result.score == 0.0
