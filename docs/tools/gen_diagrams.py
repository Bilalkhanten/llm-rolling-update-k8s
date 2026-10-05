import sys
sys.path.insert(0, ".")
from imgkit import Canvas, PAL as P

OUT = "../images/"


def pill(c, box, text, fill, outline=None, dash=False, size=20, tcolor="#0b1220", bold=True, r=14):
    c.rect(box, r, fill=fill, outline=outline, width=2, dash=dash)
    c.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), text, size, tcolor, bold=bold, anchor="mm")


def gpu_chip(c, x, y, w=92, h=44, label="GPU", dim=False):
    col = "#334155" if dim else P["teal"]
    c.rect((x, y, x + w, y + h), 8, fill=None if dim else "#0f766e", outline=col, width=2, dash=dim)
    c.text((x + w / 2, y + h / 2), label, 18, "#94a3b8" if dim else "#ccfbf1", bold=True, anchor="mm")


# ---------------------------------------------------------------- 01 cover
def cover():
    c = Canvas(1600, 840, bg=("#0b1220", "#2a1b52"))
    c.text((80, 70), "Why Does My LLM", 56, "#ffffff", bold=True)
    c.text((80, 140), "Rolling Update Hang at", 56, "#ffffff", bold=True)
    c.text((80, 210), "\u201c1 out of 3\u201d?", 56, P["amber"], bold=True)
    c.multiline((82, 314), ["A whodunit about GPU surge capacity,", "probe budgets, and graceful shutdown", "for LLM servers on Kubernetes"],
                26, P["dim"], gap=1.5)
    c.rect((80, 520, 830, 700), 14, fill="#0d1117", outline="#30363d", width=2)
    for i, col in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        c.circle((108 + i * 24, 546), 7, fill=col)
    c.text((104, 588), "$ kubectl rollout status deploy/llm", 20, "#e6edf3", mono=True)
    c.text((104, 628), "Waiting for deployment \"llm\" rollout to finish:", 19, "#e3b341", mono=True)
    c.text((104, 662), "1 out of 3 new replicas have been updated...", 19, "#e3b341", mono=True)
    # right: four nodes
    xs, ys = [900, 1230], [90, 330]
    labels = ["worker 1", "worker 2", "worker 3", "worker 4"]
    k = 0
    for yy in ys:
        for xx in xs:
            box = (xx, yy, xx + 300, yy + 210)
            if k < 3:
                c.rect(box, 16, fill=P["card"], outline=P["line"], width=2)
                c.text((xx + 22, yy + 20), labels[k], 20, P["dim"], bold=True)
                gpu_chip(c, xx + 22, yy + 62)
                pill(c, (xx + 22, yy + 126, xx + 278, yy + 176), "llm \u00b7 v1 \u00b7 Ready", P["green"], size=19)
            else:
                c.rect(box, 16, fill=None, outline=P["amber"], width=2, dash=True)
                c.text((xx + 22, yy + 20), "surge pod", 20, P["amber"], bold=True)
                gpu_chip(c, xx + 22, yy + 62, label="no GPU", dim=True, w=120)
                pill(c, (xx + 22, yy + 126, xx + 278, yy + 176), "llm \u00b7 v2 \u00b7 Pending", None, P["amber"], dash=True, tcolor=P["amber"], size=19)
            k += 1
    c.text((900, 590), "3 GPUs. 3 replicas.", 30, "#ffffff", bold=True)
    c.text((900, 636), "The default rolling update wants a 4th.", 26, P["red"], bold=True)
    c.text((80, 780), "A hands-on lab on a laptop-sized \u201cGPU cluster\u201d \u2014 full code included.", 20, P["dim"])
    return c.save(OUT + "01-cover.png")


# ---------------------------------------------------------------- 02 architecture
def architecture():
    c = Canvas(1600, 800, bg=("#0b1220", "#151a33"))
    c.text((60, 40), "The crime scene: a laptop-sized \u201cGPU cluster\u201d", 34, "#ffffff", bold=True)
    c.text((60, 92), "kind + 4 workers. Three of them advertise a fake nvidia.com/gpu: 1. No real GPU is harmed.", 21, P["dim"])
    # left column
    c.rect((60, 330, 330, 470), 16, fill=P["card"], outline=P["blue"], width=2)
    c.text((195, 372), "loadgen", 26, "#ffffff", bold=True, anchor="mm")
    c.text((195, 412), "6 streaming clients", 19, P["dim"], anchor="mm")
    c.text((195, 440), "counts truncated answers", 17, P["dim"], anchor="mm")
    c.arrow((330, 400), (410, 400), P["blue"], 3)
    c.rect((410, 340, 620, 460), 16, fill=P["card"], outline=P["purple"], width=2)
    c.text((515, 382), "Service  llm", 26, "#ffffff", bold=True, anchor="mm")
    c.text((515, 424), "port 80 \u2192 8000", 19, P["dim"], anchor="mm")
    # cluster container
    c.rect((700, 130, 1540, 760), 22, fill="#0f172a", outline=P["line"], width=2)
    c.text((730, 146), "kind cluster  \u201cllm-lab\u201d", 20, P["dim"], bold=True)
    c.rect((730, 186, 1510, 246), 12, fill=P["card2"], outline=P["line"], width=1)
    c.text((752, 216), "control-plane  (tainted \u2014 no workloads)", 19, P["dim"], anchor="lm")
    rows = [(275, True), (400, True), (525, True), (650, False)]
    names = ["llm-lab-worker", "llm-lab-worker2", "llm-lab-worker3", "llm-lab-worker4"]
    for i, (y, has) in enumerate(rows):
        box = (730, y, 1510, y + 100)
        if has:
            c.rect(box, 14, fill=P["card"], outline=P["line"], width=2)
            c.text((752, y + 20), names[i], 19, P["dim"], bold=True)
            pill(c, (752, y + 50, 1090, y + 88), "llm  (1 replica, v1, Ready)", P["green"], size=18)
            gpu_chip(c, 1380, y + 28, w=100)
            c.text((1265, y + 50), "requests", 16, P["dim"], anchor="mm")
            c.text((1265, y + 70), "nvidia.com/gpu: 1", 16, P["dim"], anchor="mm")
            c.arrow((620, 400), (728, y + 50), P["purple"], 2, head=10)
        else:
            c.rect(box, 14, fill=None, outline=P["amber"], width=2, dash=True)
            c.text((752, y + 20), names[i], 19, P["amber"], bold=True)
            c.text((752, y + 62), "no GPU advertised yet  \u2014  the \u201cspare\u201d we add later", 18, P["amber"], anchor="lm")
            gpu_chip(c, 1380, y + 28, w=100, dim=True, label="spare")
    c.text((60, 560), "How the fake GPUs work", 22, "#ffffff", bold=True)
    c.multiline((60, 600), ["kubectl patch node <n> --subresource=status \\", "  --type=json -p '[{\"op\":\"add\",", "  \"path\":\"/status/capacity/nvidia.com~1gpu\",", "  \"value\":\"1\"}]'"],
                17, "#7dd3fc", gap=1.5, mono=True)
    return c.save(OUT + "02-architecture.png")


# ---------------------------------------------------------------- 03 rollout math
def rollout_math():
    c = Canvas(1600, 800, bg=("#0b1220", "#151a33"))
    c.text((60, 40), "The default strategy asks for a GPU you don\u2019t have", 34, "#ffffff", bold=True)
    c.rect((60, 120, 760, 740), 20, fill=P["card"], outline=P["line"], width=2)
    c.text((90, 146), "Deployment defaults, replicas: 3", 24, P["dim"], bold=True)
    y = 210
    for a, b, col in [("maxSurge", "25 % of 3 = 0.75  \u2192  rounds UP    \u2192  1", P["amber"]),
                      ("maxUnavailable", "25 % of 3 = 0.75  \u2192  rounds DOWN  \u2192  0", P["red"])]:
        c.text((90, y), a, 30, col, bold=True, mono=True)
        c.text((90, y + 46), b, 21, "#e2e8f0", mono=True)
        y += 130
    c.line([(90, 480), (730, 480)], P["line"], 2)
    c.text((90, 505), "\u21d2  up to 4 pods at once", 30, "#ffffff", bold=True)
    c.text((90, 555), "\u21d2  at least 3 must stay Ready", 30, "#ffffff", bold=True)
    c.text((90, 625), "So Kubernetes needs 4 GPUs", 28, P["amber"], bold=True)
    c.text((90, 668), "to do a \u201csafe\u201d rolling update.", 28, P["amber"], bold=True)

    c.rect((820, 120, 1540, 740), 20, fill=P["card"], outline=P["line"], width=2)
    c.text((850, 146), "What your cluster actually has: 3 GPUs", 24, P["dim"], bold=True)
    for i in range(3):
        x = 860 + i * 220
        c.rect((x, 210, x + 200, 350), 14, fill="#0f172a", outline=P["teal"], width=2)
        gpu_chip(c, x + 44, 226, w=112)
        pill(c, (x + 14, 290, x + 186, 336), "old pod \u00b7 Ready", P["green"], size=17)
    c.rect((860, 400, 1080, 540), 14, fill=None, outline=P["red"], width=2, dash=True)
    c.text((970, 436), "GPU #4", 24, P["red"], bold=True, anchor="mm")
    c.text((970, 478), "does not exist", 19, P["red"], anchor="mm")
    pill(c, (1130, 420, 1500, 520), "new pod \u00b7 Pending", None, P["amber"], dash=True, tcolor=P["amber"], size=22)
    c.arrow((1120, 470), (1084, 470), P["amber"], 3, head=12)
    c.text((850, 580), "The deadlock:", 26, "#ffffff", bold=True)
    c.text((850, 622), "\u2022 old pods can\u2019t leave until a new pod is Ready", 21, "#e2e8f0")
    c.text((850, 660), "\u2022 the new pod can\u2019t start until a GPU frees up", 21, "#e2e8f0")
    c.text((850, 698), "\u2022 kubectl prints \u201c1 out of 3 new replicas\u2026\u201d forever", 21, P["amber"])
    return c.save(OUT + "03-rollout-deadlock.png")


# ---------------------------------------------------------------- 04 suspects
def suspects():
    c = Canvas(1600, 640, bg=("#0b1220", "#1b1f3b"))
    c.text((800, 44), "The three suspects", 38, "#ffffff", bold=True, anchor="mt")
    cards = [
        ("1", P["amber"], "The surge pod\nnobody can schedule", "Pending pod,\n\u201c1 out of 3 new replicas\u201d", "FailedScheduling:\nInsufficient nvidia.com/gpu"),
        ("2", P["red"], "The pod killed while\nit is still loading", "CrashLoopBackOff, or a red\nCI job (progress deadline)", "Liveness probe failed: 503\nProgressDeadlineExceeded"),
        ("3", P["purple"], "The shutdown that\neats your answers", "Half-finished answers and\n\u201cconnection refused\u201d at deploy", "SIGKILL after 30 s,\nno [DONE] in the stream"),
    ]
    for i, (n, col, title, symptom, evidence) in enumerate(cards):
        x = 60 + i * 505
        c.rect((x, 120, x + 470, 590), 20, fill=P["card"], outline=col, width=3)
        c.circle((x + 52, 176), 30, fill=col)
        c.text((x + 52, 176), n, 32, "#0b1220", bold=True, anchor="mm")
        c.multiline((x + 100, 150), title.split("\n"), 26, "#ffffff", gap=1.25, bold=True)
        c.text((x + 28, 262), "SYMPTOM", 15, col, bold=True)
        c.multiline((x + 28, 288), symptom.split("\n"), 20, "#e2e8f0", gap=1.4)
        c.text((x + 28, 388), "EVIDENCE", 15, col, bold=True)
        c.multiline((x + 28, 414), evidence.split("\n"), 19, "#7dd3fc", gap=1.4, mono=True)
    return c.save(OUT + "04-suspects.png")


# ---------------------------------------------------------------- 05 termination timeline
def timeline():
    c = Canvas(1600, 1040, bg=("#0b1220", "#151a33"))
    c.text((60, 36), "What happens to a streaming answer when its pod is terminated", 32, "#ffffff", bold=True)
    c.text((60, 84), "Numbers are from lab/sigterm_lab.py: four answers in flight with 15, 27, 39 and 51 s left.", 20, P["dim"])
    X0, K = 260, 12.4        # px per second

    def tx(t):
        return X0 + t * K

    def panel(y0, title, prestop, grace, sigkill_at, bars, exit_note):
        c.rect((40, y0, 1560, y0 + 440), 18, fill=P["card"], outline=P["line"], width=2)
        c.text((70, y0 + 20), title, 26, "#ffffff", bold=True)
        # axis
        ay = y0 + 380
        c.line([(X0, ay), (tx(100), ay)], P["dim"], 2)
        for t in range(0, 101, 10):
            c.line([(tx(t), ay), (tx(t), ay + 8)], P["dim"], 2)
            c.text((tx(t), ay + 14), f"{t}s", 16, P["dim"], anchor="mt")
        # propagation window
        c.rect((tx(0), y0 + 70, tx(3), ay), 0, fill="#3b2f0b")
        c.text((tx(3) + 8, y0 + 74), "0\u20133 s: stale routes still send new requests", 15, P["amber"])
        # preStop
        if prestop:
            c.rect((tx(0), y0 + 100, tx(prestop), y0 + 138), 8, fill="#1d4ed8")
            c.text((tx(prestop / 2), y0 + 119), "preStop", 16, "#ffffff", bold=True, anchor="mm")
        # streams
        for i, (rem, ok) in enumerate(bars):
            yy = y0 + 160 + i * 48
            c.text((70, yy + 14), f"answer {i + 1}", 17, P["dim"], anchor="lm")
            end = min(rem, sigkill_at) if sigkill_at else rem
            c.rect((tx(0), yy, tx(end), yy + 28), 8, fill=P["green"] if ok else P["red"])
            if ok:
                c.text((tx(end) + 12, yy + 14), "\u2713 complete", 17, P["green"], bold=True, anchor="lm")
            else:
                c.line([(tx(end), yy + 14), (tx(rem), yy + 14)], P["red"], 3, dash=(8, 6))
                c.text((tx(end) - 6, yy + 14), "\u2717", 26, "#ffffff", bold=True, anchor="rm")
                c.text((tx(rem) + 12, yy + 14), f"needed until {rem}s \u2014 cut off", 17, P["red"], bold=True, anchor="lm")
        # markers
        s_t = prestop
        c.line([(tx(s_t), y0 + 60), (tx(s_t), ay)], P["amber"], 3)
        c.text((tx(s_t) + 8 if s_t else tx(s_t) + 8, y0 + 340), "SIGTERM", 17, P["amber"], bold=True)
        if sigkill_at:
            c.line([(tx(sigkill_at), y0 + 60), (tx(sigkill_at), ay)], P["red"], 3)
            c.text((tx(sigkill_at) + 8, y0 + 340), "SIGKILL  (grace = 30 s)", 17, P["red"], bold=True)
        else:
            c.line([(tx(90), y0 + 60), (tx(90), ay)], P["red"], 2, dash=(8, 6))
            c.text((tx(90) - 8, y0 + 340), "SIGKILL would be here (grace = 90 s)", 15, P["red"], anchor="rt")
        l1, l2 = exit_note
        bad = "cut off" in l1 and not l1.startswith("0 of")
        col = P["red"] if bad else P["green"]
        c.rect((tx(60), y0 + 130, tx(89), y0 + 236), 14, fill="#0f172a", outline=col, width=2)
        c.text((tx(74.5), y0 + 166), l1, 22, col, bold=True, anchor="mm")
        c.text((tx(74.5), y0 + 204), l2, 19, "#e2e8f0", anchor="mm")

    panel(120, "Defaults: terminationGracePeriodSeconds 30, no preStop", 0, 30, 30,
          [(15, True), (27, True), (39, False), (51, False)], ("2 of 4 answers cut off", "5 of 6 new requests refused"))
    panel(590, "Fixed: preStop sleep 10 + terminationGracePeriodSeconds 90", 10, 90, None,
          [(15, True), (27, True), (39, True), (51, True)], ("0 of 4 answers cut off", "0 of 6 new requests refused"))
    return c.save(OUT + "05-termination-timeline.png")


# ---------------------------------------------------------------- 06 capacity swimlanes
def capacity():
    c = Canvas(1600, 700, bg=("#0b1220", "#151a33"))
    c.text((60, 36), "Three ways to roll 3 replicas on 3 GPUs", 34, "#ffffff", bold=True)
    c.text((60, 88), "Schematic \u2014 lengths are illustrative, not measured.", 19, P["dim"])
    rows = [
        ("Default\nmaxSurge 1 / maxUnavailable 0", "no spare GPU", P["red"],
         [(0.0, 1.0, "#7f1d1d", "surge pod Pending \u2014 rollout progress 0 / 3, capacity 3 Ready but nothing ever changes")]),
        ("Fix A\nmaxSurge 0 / maxUnavailable 1", "no spare GPU needed", P["amber"],
         [(0.0, 0.97, "#92400e", "2 of 3 Ready for the entire rollout (drain time + model load, per replica)"),
          (0.97, 1.0, "#166534", "3")]),
        ("Fix B\nmaxSurge 1 / maxUnavailable 0", "+ 1 spare GPU (placeholder)", P["green"],
         [(0.0, 1.0, "#166534", "3 of 3 Ready the whole time \u2014 the surge pod borrows the placeholder\u2019s GPU")]),
    ]
    x0, x1 = 60, 1540
    y = 150
    for name, sub, col, segs in rows:
        c.rect((x0, y, x1, y + 150), 18, fill=P["card"], outline=col, width=2)
        c.multiline((x0 + 26, y + 20), name.split("\n"), 22, "#ffffff", gap=1.3, bold=True)
        c.text((x0 + 26, y + 104), sub, 19, col, bold=True)
        bx0, bx1 = 520, x1 - 30
        for a, b, fill, label in segs:
            xa, xb = bx0 + a * (bx1 - bx0), bx0 + b * (bx1 - bx0)
            c.rect((xa, y + 44, xb, y + 106), 10, fill=fill)
            if len(label) > 2:
                c.text(((xa + xb) / 2, y + 75), label, 16, "#ffffff", bold=True, anchor="mm")
        c.text((bx0, y + 122), "start of rollout", 14, P["dim"])
        c.text((bx1, y + 122), "end", 14, P["dim"], anchor="ra")
        y += 175
    return c.save(OUT + "06-strategies.png")


# ---------------------------------------------------------------- 07 cheat sheet
def cheatsheet():
    rows = [
        ("New pod Pending,\n\u201c1 out of 3 new replicas\u201d", "kubectl describe pod <pending>", "FailedScheduling:\nInsufficient nvidia.com/gpu", "maxSurge 0 + maxUnavailable 1,\nor a spare GPU / placeholder pod", P["amber"]),
        ("Same message, new pod\nCrashLoopBackOff", "kubectl describe pod <new>", "Liveness probe failed: 503\n\u2192 Killing", "startupProbe with a real budget;\nliveness \u2260 readiness endpoint", P["red"]),
        ("CI red, but pods\neventually Ready", "kubectl get deploy llm -o jsonpath=\n'{.status.conditions}'", "ProgressDeadlineExceeded", "progressDeadlineSeconds \u2265 worst-case\ncold start; add --timeout + rollback", P["red"]),
        ("Users get half\nan answer at deploy", "loadgen: streams without [DONE]\nkubectl get events | grep Killing", "SIGKILL at the grace limit,\nor server exits on SIGTERM", "grace \u2265 preStop + p99 generation;\nverify your server really drains", P["purple"]),
        ("502 / connection refused\nfor a few seconds", "python3 lab/sigterm_lab.py\n(scenario B vs C)", "New requests arrive after\nthe listener closed", "preStop: sleep 5\u201315 so endpoints\nand proxies catch up", P["purple"]),
        ("SIGTERM seems ignored,\ndies after exactly 30 s", "kubectl exec <pod> --\ncat /proc/1/cmdline", "PID 1 is /bin/sh, not\nyour server", "exec-form CMD, or `exec` in\nyour entrypoint script", P["blue"]),
    ]
    H = 190 + len(rows) * 130
    c = Canvas(1600, H, bg=("#0b1220", "#151a33"))
    c.text((60, 36), "Debugging cheat sheet: stuck LLM rollouts", 36, "#ffffff", bold=True)
    cols = [60, 430, 830, 1170]
    heads = ["SYMPTOM", "WHERE TO LOOK", "WHAT YOU\u2019LL SEE", "FIX"]
    for x, h in zip(cols, heads):
        c.text((x, 110), h, 16, P["dim"], bold=True)
    y = 145
    for sym, look, see, fix, col in rows:
        c.rect((40, y, 1560, y + 116), 14, fill=P["card"], outline=P["line"], width=1)
        c.rect((40, y, 50, y + 116), 4, fill=col)
        c.multiline((cols[0], y + 22), sym.split("\n"), 20, "#ffffff", gap=1.35, bold=True)
        c.multiline((cols[1], y + 22), look.split("\n"), 16, "#7dd3fc", gap=1.5, mono=True)
        c.multiline((cols[2], y + 22), see.split("\n"), 17, "#fca5a5", gap=1.5, mono=True)
        c.multiline((cols[3], y + 22), fix.split("\n"), 18, "#bbf7d0", gap=1.5)
        y += 130
    return c.save(OUT + "07-cheatsheet.png")


for f in (cover, architecture, rollout_math, suspects, timeline, capacity, cheatsheet):
    print(f.__name__, f())
