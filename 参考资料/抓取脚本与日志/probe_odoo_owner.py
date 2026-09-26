# -*- coding: utf-8 -*-
"""验证 Odoo / 其他项目的库存模型是否原生支持货权分离（owner / 货主 维度）"""
import os, re, ssl, urllib.request, urllib.parse, time, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research)"}
OUT = r"D:\货灵云仓\_research\models"
os.makedirs(OUT, exist_ok=True)


def raw(repo, branch, path):
    url = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, branch, path)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return r.read().decode("utf-8", "ignore")


def save(name, txt):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(txt)


log = []

# 1. Odoo stock.quant 是否含 owner 维度
for br in ["18.0", "17.0", "16.0"]:
    try:
        t = raw("odoo/odoo", br, "addons/stock/models/stock_quant.py")
        hits = [l.strip() for l in t.splitlines()
                if re.search(r"owner|Owner", l) and ("=" in l or "def " in l)]
        save("odoo_stock_quant_%s.py" % br, t)
        log.append("odoo %s stock_quant.py len=%d owner-hits=%d" % (br, len(t), len(hits)))
        log.extend(["    " + h[:160] for h in hits[:25]])
        break
    except Exception as e:
        log.append("odoo %s FAIL %s" % (br, e))

# 2. Odoo stock.move / stock.lot 是否含 owner
for br in ["18.0"]:
    for f in ["stock_move.py", "stock_lot.py", "stock_location.py"]:
        try:
            t = raw("odoo/odoo", br, "addons/stock/models/" + f)
            hits = [l.strip() for l in t.splitlines() if re.search(r"owner", l, re.I) and "=" in l]
            save("odoo_%s_%s" % (f.replace(".py", ""), br), t)
            log.append("odoo %s %s owner-hits=%d" % (br, f, len(hits)))
            log.extend(["    " + h[:160] for h in hits[:12]])
        except Exception as e:
            log.append("odoo %s %s FAIL %s" % (br, f, e))

# 3. InvenTree 是否有 owner / customer 维度的库存
for br in ["master"]:
    for p in ["InvenTree/stock/models.py", "InvenTree/stock/serializers.py"]:
        try:
            t = raw("inventree/InvenTree", br, p)
            hits = [l.strip() for l in t.splitlines()
                    if re.search(r"owner|customer|belongs_to", l, re.I) and "=" in l]
            log.append("InvenTree %s owner-hits=%d" % (p, len(hits)))
            log.extend(["    " + h[:160] for h in hits[:15]])
        except Exception as e:
            log.append("InvenTree %s FAIL %s" % (p, e))

# 4. openboxes 的库存/批次模型（Groovy domain）
for br in ["develop"]:
    for p in ["grails-app/domain/org/pih/warehouse/inventory/Transaction.groovy",
              "grails-app/domain/org/pih/warehouse/core/Location.groovy",
              "grails-app/domain/org/pih/warehouse/product/Product.groovy",
              "grails-app/domain/org/pih/warehouse/inventory/InventoryItem.groovy"]:
        try:
            t = raw("openboxes/openboxes", br, p)
            save("openboxes_" + p.split("/")[-1], t)
            log.append("openboxes OK %s len=%d" % (p.split("/")[-1], len(t)))
        except Exception as e:
            log.append("openboxes FAIL %s : %s" % (p, e))

with open(os.path.join(OUT, "_model_probe.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log))
print("\n".join(log))
