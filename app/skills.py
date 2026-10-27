"""A small skill dictionary and helpers to find skills inside free text."""

import re

# canonical skill name -> alternate spellings found in resumes and job posts
SKILLS: dict[str, list[str]] = {
    # languages
    "Python": ["python"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js", "es6"],
    "TypeScript": ["typescript"],
    "C++": ["c++", "cpp"],
    "SQL": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
    "R": ["r programming", "r language"],
    # machine learning / ai
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "neural network", "neural networks"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "opencv", "image processing"],
    "LLMs": ["llm", "llms", "large language model", "large language models", "gpt"],
    "Generative AI": ["generative ai", "genai", "gen ai"],
    "Prompt Engineering": ["prompt engineering", "prompting"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    "LangChain": ["langchain"],
    "Vector Databases": ["vector database", "vector databases", "faiss", "pinecone", "chromadb", "chroma"],
    "TensorFlow": ["tensorflow", "keras"],
    "PyTorch": ["pytorch", "torch"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "Hugging Face": ["hugging face", "huggingface", "transformers"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Data Analysis": ["data analysis", "data analytics", "eda", "exploratory data analysis"],
    "Data Visualization": ["data visualization", "matplotlib", "seaborn", "power bi", "tableau"],
    "Statistics": ["statistics", "statistical analysis", "probability"],
    # backend / web
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Django": ["django"],
    "Node.js": ["node.js", "nodejs", "node", "express"],
    "React": ["react", "react.js", "reactjs", "next.js", "nextjs"],
    "REST APIs": ["rest api", "rest apis", "restful", "api development"],
    "HTML/CSS": ["html", "css", "tailwind"],
    "MongoDB": ["mongodb", "mongo"],
    # tooling / cloud
    "Git": ["git", "github", "gitlab"],
    "Docker": ["docker", "containerization"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "sagemaker"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud", "vertex ai"],
    "Linux": ["linux", "bash", "shell scripting"],
    "CI/CD": ["ci/cd", "github actions", "jenkins"],
    "MLOps": ["mlops", "mlflow", "model deployment"],
    # soft skills
    "Communication": ["communication", "communication skills"],
    "Teamwork": ["teamwork", "team player", "collaboration"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical skills"],
}


def _build_pattern(alias: str) -> re.Pattern:
    # \b does not work around symbols like "c++" or "ci/cd", so use lookarounds instead
    return re.compile(rf"(?<![\w+#]){re.escape(alias)}(?![\w+#])", re.IGNORECASE)


_PATTERNS = {
    skill: [_build_pattern(alias) for alias in aliases]
    for skill, aliases in SKILLS.items()
}


def extract_skills(text: str) -> set[str]:
    """Return the canonical names of all known skills mentioned in the text."""
    return {
        skill
        for skill, patterns in _PATTERNS.items()
        if any(pattern.search(text) for pattern in patterns)
    }
