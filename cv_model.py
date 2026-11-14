"""Data helpers for the CV app. No GUI code here, so it can be tested on its own."""
import json
import re
from pathlib import Path

ITEM_TYPES = {
    "bullet": "Madde işareti",
    "entry": "Başlık / kurum / tarih",
    "labeled": "Etiketli satır",
    "para": "Paragraf",
}

ITEM_FIELDS = {
    "bullet": [("text", "Madde metni"), ("url", "Bağlantı (isteğe bağlı)")],
    "entry": [("title", "Başlık"), ("org", "Kurum"), ("dates", "Tarih")],
    "labeled": [("label", "Etiket"), ("text", "Metin")],
    "para": [("text", "Metin")],
}


def empty_cv():
    return {"name": "", "title": "", "contact": [], "sections": []}


def load_cv(path):
    p = Path(path)
    if not p.exists():
        return empty_cv()
    return json.loads(p.read_text(encoding="utf-8"))


def save_cv(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def next_copy_path(path):
    """Return the first free sibling name: my_tr.json -> my_tr_1.json, my_tr_2.json, ...
    An existing _N suffix is replaced, so repeated copies do not stack suffixes."""
    p = Path(path)
    base = re.sub(r"_\d+$", "", p.stem)
    n = 1
    while True:
        candidate = p.with_name(f"{base}_{n}{p.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def split_contact(contact):
    """Turn header segments back into (location, email, linkedin, github)."""
    location_parts, email, linkedin, github = [], "", "", ""
    for seg in contact:
        url = seg.get("url", "")
        if url.startswith("mailto:"):
            email = url[len("mailto:"):]
        elif "linkedin.com" in url:
            linkedin = url
        elif "github.com" in url:
            github = url
        elif not url:
            location_parts.append(seg.get("text", ""))
    pieces = [p.strip() for p in "".join(location_parts).split("|")]
    location = " | ".join(p for p in pieces if p)
    return location, email, linkedin, github


def build_contact(location, email, linkedin, github):
    """Build header segments from the four form fields."""
    items = []
    if location.strip():
        items.append({"text": location.strip()})
    if email.strip():
        items.append({"text": email.strip(), "url": "mailto:" + email.strip()})
    if linkedin.strip():
        items.append({"text": "LinkedIn", "url": linkedin.strip()})
    if github.strip():
        items.append({"text": "GitHub", "url": github.strip()})
    segments = []
    for i, item in enumerate(items):
        if i:
            segments.append({"text": " | "})
        segments.append(item)
    return segments


def new_item(item_type="bullet"):
    return {"type": item_type, **{key: "" for key, _ in ITEM_FIELDS[item_type]}}


def describe_item(item):
    t = item.get("type", "bullet")
    if t == "entry":
        return f"{item.get('title', '')} | {item.get('org', '')} ({item.get('dates', '')})"
    if t == "labeled":
        return f"{item.get('label', '')}: {item.get('text', '')}"
    if t == "para":
        return item.get("text", "")[:90]
    return "• " + item.get("text", "")[:90]


def clean_item(item):
    """Keep only the fields this item type uses; drop an empty optional url."""
    out = {"type": item["type"]}
    for key, _ in ITEM_FIELDS[item["type"]]:
        value = item.get(key, "")
        if key == "url" and not value:
            continue
        out[key] = value
    return out


# ---------- Job-ad tailoring (offline keyword matching) ----------
import copy
import re

KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "Golang", "Dart", "SQL", "PL/SQL",
    "React", "React.js", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring", "Spring Boot",
    "Flutter", "Android", "iOS", "Docker", "Kubernetes", "Git", "GitHub", "CI/CD", "Linux",
    "AWS", "Azure", "Google Cloud", "PostgreSQL", "MySQL", "SQL Server", "MongoDB", "Redis", "Oracle",
    "REST", "RESTful", "GraphQL", "OAuth", "OIDC", "Webhook", "Celery", "RabbitMQ", "Kafka",
    "Machine Learning", "Deep Learning", "NLP", "LLM", "RAG", "Prompt Engineering", "Generative AI",
    "OpenCV", "TensorFlow", "PyTorch", "scikit-learn", "XGBoost", "YOLO", "YOLOv8", "Pandas", "NumPy",
    "Power BI", "Excel", "Scrum", "Agile", "Jira", "Unity", "Selenium", "Figma", "HTML", "CSS",
    "Bootstrap", "jQuery", "Swift", "Kotlin", "Rust", "PHP", "Laravel", ".NET", "Blazor", "Groq",
]

_SKILL_HEADINGS = ("beceri", "skill", "yetenek", "competenc")


def _term_pattern(term):
    return re.compile(r"(?<![\w.+#])" + re.escape(term) + r"(?![\w+#])", re.IGNORECASE)


def find_terms(text, terms=None):
    """Return the known terms that appear in text, in the order of KEYWORDS."""
    terms = terms or KEYWORDS
    return [t for t in terms if _term_pattern(t).search(text or "")]


def extract_keywords(ad_text):
    return find_terms(ad_text)


def cv_text(cv):
    parts = [cv.get("title", "")]
    for seg in cv.get("contact", []):
        parts.append(seg.get("text", ""))
    for section in cv.get("sections", []):
        for item in section.get("items", []):
            parts.extend(str(v) for k, v in item.items() if k != "type")
    return "\n".join(parts)


def analyze(cv, ad_text):
    """Compare a job ad with the CV. Returns matched and missing terms."""
    ad_terms = extract_keywords(ad_text)
    in_cv = set(find_terms(cv_text(cv), ad_terms))
    matched = [t for t in ad_terms if t in in_cv]
    missing = [t for t in ad_terms if t not in in_cv]
    return {"matched": matched, "missing": missing}


def _count_matches(text, terms):
    return sum(1 for t in terms if _term_pattern(t).search(text or ""))


def tailor(cv, matched):
    """Return a copy of cv with matched skills first and relevant entries moved up.
    Nothing is added; only the order changes."""
    out = copy.deepcopy(cv)
    if not matched:
        return out
    for section in out.get("sections", []):
        heading = section.get("heading", "").lower()
        if any(h in heading for h in _SKILL_HEADINGS):
            for item in section.get("items", []):
                if item.get("type") != "labeled":
                    continue
                parts = [p.strip() for p in item.get("text", "").split(",") if p.strip()]
                hit = [p for p in parts if any(_term_pattern(t).search(p) for t in matched)]
                rest = [p for p in parts if p not in hit]
                if hit:
                    item["text"] = ", ".join(hit + rest)
        else:
            # group entries with their bullets, then sort groups by relevance (stable)
            groups, current = [], []
            for item in section.get("items", []):
                if item.get("type") == "entry" and current:
                    groups.append(current)
                    current = []
                current.append(item)
            if current:
                groups.append(current)
            if len(groups) > 1:
                def score(group):
                    text = " ".join(" ".join(str(v) for k, v in it.items() if k != "type") for it in group)
                    return _count_matches(text, matched)
                groups.sort(key=score, reverse=True)
                section["items"] = [it for g in groups for it in g]
    return out
