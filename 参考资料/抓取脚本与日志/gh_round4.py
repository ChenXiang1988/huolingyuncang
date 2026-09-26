# -*- coding: utf-8 -*-
"""第四轮：补搜国内三方云仓关键词 + 拉取 JeeWMS 目录树验证模型真实性"""
import json, os, ssl, time, urllib.request, urllib.parse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research)", "Accept": "application/vnd.github+json"}
OUT = r"D:\货灵云仓\_research"
log = []


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


# ---------- A. 补搜 ----------
QS = [
    "云仓 in:name,description",
    "三方仓储 in:name,description",
    "3pl in:name,description stars:>50",
    "货主 in:name,description stars:>20",
    "仓储管理系统 in:name,description",
    "wms 货主 in:name,description",
    "billing warehouse in:name,description stars:>30",
    "warehouse billing in:name,description",
    "multi-tenant warehouse in:name,description",
    "pda 仓库 in:name,description",
]
found = {}
for q in QS:
    try:
        d = fetch("https://api.github.com/search/repositories?q=" + urllib.parse.quote(q) +
                  "&sort=stars&order=desc&per_page=30")
        n = len(d.get("items", []))
        log.append("q=%-45s n=%d" % (q, n))
        for it in d.get("items", []):
            found[it["full_name"]] = (it["stargazers_count"], it.get("language"),
                                      (it.get("license") or {}).get("spdx_id"),
                                      (it.get("pushed_at") or "")[:10],
                                      (it.get("description") or "")[:120])
    except Exception as e:
        log.append("q=%-45s FAIL %s" % (q, e))
    time.sleep(7)

log.append("\n--- 补搜命中（星数>=30）---")
for k, v in sorted(found.items(), key=lambda x: -x[1][0]):
    if v[0] >= 30:
        log.append("%-42s | %6d | %-10s | %-12s | %s | %s" % (k[:42], v[0], v[1], v[2], v[3], v[4]))

# ---------- B. JeeWMS 目录树 ----------
def tree(repo, branch, name):
    try:
        d = fetch("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (repo, branch))
        paths = [t["path"] for t in d.get("tree", []) if t["type"] == "blob"]
        with open(os.path.join(OUT, "tree_%s.txt" % name), "w", encoding="utf-8") as f:
            f.write("\n".join(paths))
        log.append("TREE %s files=%d" % (repo, len(paths)))
        return paths
    except Exception as e:
        log.append("TREE %s FAIL %s" % (repo, e))
        return []


p = tree("erzhongxmu/JeeWMS", "master", "JeeWMS")
if p:
    import re
    keys = ["owner|huozhu|customer|cus_|client", "fee|charge|billing|price|cost|settle|account",
            "batch|lot|expire|valid", "pda|app|mobile|terminal", "task|wave|pick"]
    for k in keys:
        hits = [x for x in p if re.search(k, x, re.I)]
        log.append("  [%s] hits=%d" % (k, len(hits)))
        for h in hits[:12]:
            log.append("      " + h)

with open(os.path.join(OUT, "round4.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log))
print("done")
