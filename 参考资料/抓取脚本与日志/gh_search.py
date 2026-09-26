# -*- coding: utf-8 -*-
"""GitHub 开源 WMS 海选脚本：多组关键词 -> 去重 -> 落盘 JSON"""
import json, ssl, time, urllib.request, urllib.parse, os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = {"User-Agent": "Mozilla/5.0 (research)", "Accept": "application/vnd.github+json"}

QUERIES = [
    "wms in:name,description",
    "warehouse management in:name,description",
    "warehouse management system in:name,description",
    "inventory warehouse in:name,description",
    "仓储管理 in:name,description",
    "仓库管理 in:name,description",
    "仓库管理系统 in:name,description",
    "WMS 仓库 in:name,description",
    "supply chain warehouse java in:name,description",
    "logistics warehouse in:name,description",
]


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


def search(q, per_page=50):
    url = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(q) + \
          "&sort=stars&order=desc&per_page=%d" % per_page
    try:
        data = fetch(url)
    except Exception as e:
        print("  !! fail:", q, e)
        return []
    return data.get("items", [])


all_repos = {}
for q in QUERIES:
    items = search(q)
    print("query=%-55s hits=%d" % (q, len(items)))
    for it in items:
        all_repos[it["full_name"]] = {
            "full_name": it["full_name"],
            "html_url": it["html_url"],
            "description": (it.get("description") or "")[:300],
            "stars": it["stargazers_count"],
            "forks": it["forks_count"],
            "open_issues": it["open_issues_count"],
            "language": it.get("language"),
            "license": (it.get("license") or {}).get("spdx_id"),
            "created_at": it.get("created_at"),
            "pushed_at": it.get("pushed_at"),
            "updated_at": it.get("updated_at"),
            "topics": it.get("topics") or [],
            "archived": it.get("archived"),
            "size_kb": it.get("size"),
        }
    time.sleep(2)  # 未认证 API 限流

out = sorted(all_repos.values(), key=lambda x: -x["stars"])
os.makedirs(r"D:\货灵云仓\_research", exist_ok=True)
with open(r"D:\货灵云仓\_research\gh_candidates.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("\nTOTAL UNIQUE:", len(out))
for r in out[:60]:
    print("%-45s %6d  %-12s %-15s %s" % (
        r["full_name"][:45], r["stars"], r["language"], r["license"], (r["pushed_at"] or "")[:10]))
