from cv_model import *
import json
d = json.load(open("example_tr.json", encoding="utf-8"))
loc, em, li, gh = split_contact(d["contact"])
print("split:", loc, "|", em, "|", li, "|", gh)
seg = build_contact(loc, em, li, gh)
assert "".join(x["text"] for x in seg).replace(" ","") == "".join(x["text"] for x in d["contact"]).replace(" ",""), "text differs"
assert [x.get("url") for x in seg if x.get("url")] == [x.get("url") for x in d["contact"] if x.get("url")]
print("contact round-trip OK")
print(describe_item(d["sections"][1]["items"][0]))
print(describe_item(d["sections"][0]["items"][0]) if d["sections"][0]["items"] else "")
it = clean_item({"type": "bullet", "text": "x", "url": ""})
assert it == {"type": "bullet", "text": "x"}, it
print("clean OK", it)
