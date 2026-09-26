# -*- coding: utf-8 -*-
"""第三轮：拉取重点候选的 README（走 raw，不耗 API 额度）"""
import os, ssl, urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research)"}
OUT = r"D:\货灵云仓\_research\readmes"
os.makedirs(OUT, exist_ok=True)

TARGETS = [
    ("GreaterWMS", "GreaterWMS/GreaterWMS", ["main", "master", "develop"]),
    ("open-wes", "jingsewu/open-wes", ["main", "master"]),
    ("ModernWMS", "fjykTec/ModernWMS", ["master", "main"]),
    ("wms-ruoyi", "zccbbg/wms-ruoyi", ["master", "main"]),
    ("openboxes", "openboxes/openboxes", ["develop", "master", "main"]),
    ("org.openwms", "openwms/org.openwms", ["master", "main"]),
    ("InvenTree", "inventree/InvenTree", ["master", "main"]),
    ("OCA-wms", "OCA/wms", ["18.0", "17.0", "16.0", "master"]),
    ("JeeWMS", "erzhongxmu/JeeWMS", ["master", "main"]),
    ("KopSoftWms", "lysilver/KopSoftWms", ["master", "main"]),
    ("mywms", "wms2/mywms", ["master", "main"]),
    ("oms-erp", "FJ-OMS/oms-erp", ["master", "main"]),
    ("SPMS", "s-pms/SPMS-Server", ["master", "main"]),
    ("yeqifu-warehouse", "yeqifu/warehouse", ["master", "main"]),
    ("fleetbase", "fleetbase/fleetbase", ["main", "master"]),
    ("crbnos-carbon", "crbnos/carbon", ["main", "master"]),
    ("s-pms2", "qq283335746/Wms", ["master", "main"]),
    ("smowms", "comsmobiler/SmoWMS", ["master", "main"]),
    ("RuoYi-WMS-VUE", "zccbbg/RuoYi-WMS-VUE", ["master", "main"]),
    ("jshERP", "jishenghua/jshERP", ["master", "main"]),
]

report = []
for name, repo, branches in TARGETS:
    got = False
    for br in branches:
        for fname in ["README.md", "readme.md", "README.MD", "README.rst", "README"]:
            url = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, br, fname)
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
                    txt = r.read().decode("utf-8", "ignore")
                if len(txt) < 50:
                    continue
                with open(os.path.join(OUT, name + ".md"), "w", encoding="utf-8") as f:
                    f.write("# SOURCE: %s  branch=%s file=%s\n\n" % (repo, br, fname))
                    f.write(txt)
                report.append("OK   %-18s %-28s br=%-8s len=%d" % (name, repo, br, len(txt)))
                got = True
                break
            except Exception as e:
                continue
        if got:
            break
    if not got:
        report.append("FAIL %-18s %-28s (no README found)" % (name, repo))

with open(os.path.join(OUT, "_result.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(report))
print("\n".join(report))
