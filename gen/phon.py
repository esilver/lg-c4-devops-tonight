"""phon.py : pronunciations (ARPAbet with stress) for every spoken line -> ../src/phon.json  [[word, "PH PH ..."], ...] per line"""
import json, re, cmudict
D = cmudict.dict()
LINES = [
 "Good evening, this is DevOps Tonight. I'm Paige Duty, and yes, I am on call.",
 "And I'm Cy Dekar. It is 2026, and production is, for the moment, up.",
 "Our top story: an AI agent opened forty pull requests overnight. A second agent approved them. A human is now being paged.",
 "Meanwhile, a routine Friday deploy is under way in us-east-1. Dee Ploy is at the scene. Dee?",
 "Thanks, Cy. The pipeline behind me has been green for nine minutes, and nobody here trusts it.",
 "Engineers have checked the dashboards, the rollback plan, and DNS. Sources say it is always DNS.",
 "Dee, did anyone suggest waiting until Monday?",
 "One person did, Cy. They have been moved to the platform team. Back to you.",
 "Brave work. Now the cloud forecast, with Sunny Uptime.",
 "Thanks, Paige. Pods are stuck Pending across the north while the autoscaler thinks about it.",
 "In the south, scattered 503s with a chance of retries. Four nines along the coast, and a high of nine thousand dollars in egress.",
 "Joining us is Y. A. Mel, Staff YAML Engineer. With agents writing the config now, is your job safe?",
 "Cy, the agent writes four thousand lines of YAML a day. Someone still has to find the one wrong indent.",
 "Chilling. Thank you for your time.",
 "That's all for tonight. Remember: you build it, you run it, and FinOps will ask what it cost.",
 "From all of us in the control plane, good night, and may your pager stay quiet.",
]
OV = {  # words the dictionary lacks, abbreviations, numbers
 "devops": "D EH1 V AA2 P S", "finops": "F IH1 N AA2 P S", "dekar": "D IH0 K AA1 R", "cy": "S AY1", "yaml": "Y AE1 M AH0 L", "uptime": "AH1 P T AY2 M",
 "autoscaler": "AO1 T OW0 S K EY2 L ER0", "config": "K AA1 N F IH0 G", "retries": "R IY1 T R AY2 Z", "2026": "T W EH1 N T IY0 T W EH1 N T IY0 S IH1 K S", "us-east-1": "Y UW1 EH1 S IY1 S T W AH1 N",
 "dns": "D IY1 EH1 N EH1 S", "503s": "F AY1 V OW1 TH R IY1 Z", "ai": "EY1 AY1", "y": "W AY1", "a.": "EY1", "i'm": "AY1 M", "that's": "DH AE1 T S",
 # reduced forms of little words, as they are actually said mid-sentence
 "the": "DH AH0", "a": "AH0", "an": "AH0 N", "and": "AH0 N D", "is": "IH0 Z", "it": "IH0 T", "in": "IH0 N", "of": "AH0 V", "for": "F ER0", "to": "T AH0",
 "has": "HH AE0 Z", "have": "HH AE0 V", "been": "B IH0 N", "are": "ER0", "with": "W IH0 DH", "at": "AE0 T", "am": "AE0 M", "will": "W AH0 L", "them": "DH AH0 M",
 "from": "F R AH0 M", "your": "Y ER0", "us": "AH0 S", "did": "D IH1 D", "you": "Y UW1", "what": "W AH1 T", "tonight": "T AH0 N AY1 T", "duty": "D UW1 T IY0", "good": "G UH1 D",
}
out = []
for ln in LINES:
    row = []
    for w in ln.split(" "):
        k = w.lower().strip(",.?!:;")
        if w.lower() == "a." : k = "a."
        p = OV.get(k) or (D.get(k) and " ".join(D[k][0]))
        assert p, f"no pronunciation for {w!r}"
        row.append([w, p])
    out.append(row)
json.dump(out, open("../src/phon.json", "w")); 
for r in out: print(" | ".join(f"{w}={p}" for w, p in r)); print()
