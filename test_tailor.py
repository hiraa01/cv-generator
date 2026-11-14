import json
from cv_model import analyze, tailor, extract_keywords
cv = json.load(open("example_tr.json", encoding="utf-8"))
ad = """Aranan: Python ve Django bilgisi, Docker deneyimi, REST API tasarımı.
Flutter ve Kubernetes tecrübesi artı. AWS bilgisi olmalı. C# kullanımı avantaj."""
print("ad terms:", extract_keywords(ad))
r = analyze(cv, ad)
print("matched:", r["matched"])
print("missing:", r["missing"])
t = tailor(cv, r["matched"])
print("skills before:", cv["sections"][1]["items"][0]["text"])
print("skills after :", t["sections"][1]["items"][0]["text"])
assert cv["sections"][1]["items"][0]["text"] == json.load(open("example_tr.json", encoding="utf-8"))["sections"][1]["items"][0]["text"], "original mutated"
print("original untouched OK")
# check false positives: "Go" inside words, "C#" should not match "C++" text
print("no false Go:", "Go" not in extract_keywords("Google ile çalıştı"))
print("R in REST:", "REST" in extract_keywords("RESTful API"))
