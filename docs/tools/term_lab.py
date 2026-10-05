import re, sys
sys.path.insert(0, ".")
from imgkit import terminal

raw = open("../../lab/sample-output.txt").read().rstrip("\n").split("\n")
lines = ["{g}${/} python3 lab/sigterm_lab.py"]
for l in raw:
    if not l.strip():
        lines.append(""); continue
    if l.startswith("Running"):
        lines.append("{d}" + l + "{/}")
    elif re.match(r"^\[[A-D]\]", l):
        col = "w"
        if "SIGKILL" in l: col = "r"
        elif "cut off" in l:
            col = "r" if not " 0 cut off" in l else "g"
        elif "SIGTERM sent" in l: col = "y"
        elif "Terminating" in l: col = "c"
        lines.append("{" + col + "}" + l + "{/}")
    elif l.startswith("  scenario") or l.startswith("---"):
        lines.append("{d}" + l + "{/}")
    elif re.match(r"^[A-D] ", l):
        bad = re.search(r"\s(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$", l)
        cut = int(bad.group(2)); refused = int(bad.group(4))
        col = "g" if (cut == 0 and refused == 0) else ("r" if cut else "y")
        lines.append("{" + col + "}" + l + "{/}")
    else:
        lines.append(l)
terminal(lines, "../images/t1-sigterm-lab.png", title="llm-rollout-lab — python3 lab/sigterm_lab.py")
print("ok", len(lines))
