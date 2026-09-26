# -*- coding: utf-8 -*-
"""第二轮：topic 精确搜索 + 手工候选清单校验"""
import json, ssl, time, urllib.request, urllib.parse, os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research)", "Accept": "application/vnd.github+json"}
OUT = r"D:\货灵云仓\_research"


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


def search(q, per_page=50):
    url = ("https://api.github.com/search/repositories?q=" + urllib.parse.quote(q) +
           "&sort=stars&order=desc&per_page=%d" % per_page)
    try:
        return fetch(url).get("items", [])
    except Exception as e:
        print("  !! fail:", q, e)
        return []


TOPIC_QUERIES = [
    "topic:wms",
    "topic:warehouse",
    "topic:warehouse-management",
    "topic:inventory-management",
    "topic:supply-chain stars:>200",
    "topic:erp stars:>500",
    "topic:wms-java",
    "topic:logistics stars:>500",
]
NAME_QUERIES = [
    "wms in:name stars:>100",
    "warehouse in:name stars:>200",
    "inventory in:name stars:>1000",
    "仓库 in:name,description stars:>50",
    "仓储 in:name,description stars:>50",
    "wms in:name,description language:Java stars:>50",
    "wms in:name,description language:Python stars:>50",
    "warehouse management system in:readme stars:>100",
]

# 手工候选：业界已知 / 常见，逐个校验真实存在与活跃度
MANUAL = [
    "openboxes/openboxes",
    "inventree/InvenTree",
    "openwms/org.openwms",
    "openwms/org.openwms.core",
    "openwms/org.openwms.tms",
    "frappe/erpnext",
    "odoo/odoo",
    "yangzongzhuan/RuoYi",
    "jeecgboot/JeecgBoot",
    "apache/ofbiz",
    "akaunting/akaunting",
    "invoiceninja/invoiceninja",
    "metasfresh/metasfresh",
    "dolibarr/dolibarr",
    "ghislieri/WMS",
    "jhipster/jhipster-sample-app",
    "paulc4/wms",
    "ross-davey/wms",
    "snipe/snipe-it",
    "eramba/eramba",
    "openboxes/grails-warehouse",
    "hschneid/warehouse",
    "joewandy/wms",
    "kartoza/django-wms",
    "norkunas/cin7",
    "blueseaspl/wms",
    "violet-wms/violet",
    "wms-systems/wms",
    "sap-labs/wms",
    "openlogistics/open-wms",
    "novatecconsulting/wms",
    "odoo-turkey/wms",
    "skfaisal93/wms",
]

repos = {}


def add(it):
    fn = it["full_name"]
    if fn not in repos:
        repos[fn] = {
            "full_name": fn,
            "html_url": it["html_url"],
            "description": (it.get("description") or "")[:400],
            "stars": it["stargazers_count"],
            "forks": it["forks_count"],
            "open_issues": it["open_issues_count"],
            "language": it.get("language"),
            "license": (it.get("license") or {}).get("spdx_id"),
            "created_at": it.get("created_at"),
            "pushed_at": it.get("pushed_at"),
            "topics": it.get("topics") or [],
            "archived": it.get("archived"),
            "size_kb": it.get("size"),
            "homepage": it.get("homepage"),
        }


for q in TOPIC_QUERIES + NAME_QUERIES:
    items = search(q)
    print("q=%-60s n=%d" % (q, len(items)))
    for it in items:
        add(it)
    time.sleep(2)

# 手工候选逐个查
manual_hits = {}
for fn in MANUAL:
    try:
        d = fetch("https://api.github.com/repos/" + fn)
        if "full_name" in d:
            manual_hits[fn] = {
                "full_name": d["full_name"],
                "html_url": d["html_url"],
                "description": (d.get("description") or "")[:400],
                "stars": d["stargazers_count"],
                "forks": d["forks_count"],
                "open_issues": d["open_issues_count"],
                "language": d.get("language"),
                "license": (d.get("license") or {}).get("spdx_id"),
                "created_at": d.get("created_at"),
                "pushed_at": d.get("pushed_at"),
                "topics": d.get("topics") or [],
                "archived": d.get("archived"),
                "size_kb": d.get("size"),
                "homepage": d.get("homepage"),
            }
            print("OK   %-40s %6d %s" % (fn, d["stargazers_count"], (d.get("pushed_at") or "")[:10]))
        else:
            print("MISS %-40s %s" % (fn, d.get("message")))
    except Exception as e:
        print("ERR  %-40s %s" % (fn, e))
    time.sleep(1.2)

for k, v in manual_hits.items():
    repos.setdefault(k, v)

out = sorted(repos.values(), key=lambda x: -x["stars"])
with open(os.path.join(OUT, "gh_round2.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

lines = ["TOTAL: %d\n" % len(out)]
for r in out:
    lines.append("%-45s | %6d | %-12s | %-12s | %s | %s" % (
        r["full_name"][:45], r["stars"], r["language"], r["license"],
        (r["pushed_at"] or "")[:10], (r["description"] or "").replace("\n", " ")[:130]))
with open(os.path.join(OUT, "gh_round2.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\nWROTE", len(out))
