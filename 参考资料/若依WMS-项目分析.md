# 若依 WMS（`wms-ruoyi`）项目分析

> 分析对象：`github.com/zccbbg/wms-ruoyi`（Gitee 同源，同一仓库）
> 分析日期：2026-09-25
> 取材：**本地克隆实读**。`master`（= `lite`）与 `advance` 双分支全量源码
> 版本：`5.2.0` · 克隆时 HEAD 提交 `ccc78f7 docs(readme): 更新在线体验链接`

---

## 〇、两份源码的关系，以及上一版报告的证据升级

### 你给的那个地址与我给出的真身

| | 地址 | 状态 |
|---|---|---|
| 你给的 | `https://www.gitcc.com/suicidepalm/gibbon-wms` | **不可读**。`www.gitcc.com` 是自建 GitLab（响应头 `X-Gitlab-Meta`），全站 302 跳 `/users/sign_in`，另叠宝塔网页防护 |
| 真身 | `https://github.com/zccbbg/wms-ruoyi` · `https://gitee.com/zccbbg/wms-ruoyi` | **已克隆到本地实读** |

`suicidepalm/gibbon-wms` 在 GitHub／Gitee／GitCode 三站均 404，GitHub 用户 `suicidepalm` 本身不存在。

**推论（依据：描述文本逐字重合）**：gitcc 上的 `gibbon-wms` / `gibbon-wms-plat` 是若依 WMS 的二次打包改名版。**猜测（明说是猜）**：gitcc 属于「注册后取源码」的分发站。这两条我无法证实，因为那侧完全不可读。

### 本次证据升级

上一版报告基于 GitHub 接口与 raw 文件**在线读取**，因此有两处我标了「判断不了」。**本次克隆了完整源码，那两条已做实，并且做实的结果比上一版更难看**（见 P3、P6）。凡标「事实」的断言，下面都给了**文件路径与行号**。

### 克隆规模（实测）

| 项 | 数值 |
|---|---|
| Java 文件总数 | 486 |
| 业务模块 `ruoyi-admin-wms` 代码行 | 7,707 行 |
| 业务表 / 系统表 | 16 / 19（`lite`）；18 / 19（`advance`） |
| `wms.sql` 种子数据 | 102 条菜单记录 |
| 业务控制器 | 16 个（`lite`）／18 个（`advance`） |

---

## 一、定位：它是「单货主自营库存台账」，不是「一仓 N 货主的三方云仓」

判定依据是主键结构，不是文档措辞。

**`wms_inventory` 完整建表语句（`script/sql/wms.sql`，原文照录）：**

```sql
CREATE TABLE `wms_inventory`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `sku_id` bigint(20) NULL DEFAULT NULL COMMENT '规格ID',
  `warehouse_id` bigint(20) NULL DEFAULT NULL COMMENT '所属仓库',
  `quantity` decimal(20, 2) NULL DEFAULT NULL COMMENT '库存',
  `remark` varchar(255) ...,
  `create_by` / `create_time` / `update_by` / `update_time` ...,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB ... COMMENT = '库存表';
```

**库存的全部维度就是「规格 + 仓库」两个**。没有货主、没有货权、没有批次（`lite`）、没有库位、没有库存状态（可用/占用/冻结/在途）。

`wms_merchant` 的字典定义（`sys_dict_data`，字典键 `merchant_type`）：
`0 客户` / `1 供应商` / `3 客户/供应商`——**这是往来单位，不是货主**。

**对本项目的直接含义**：它连「同一仓库同一规格、分属两个货主的两笔独立库存」都装不下。加字段解决不了——库存主键与全部单据口径都得重建。

### 附带发现：全库零唯一约束（事实）

```
grep -c "UNIQUE KEY" script/sql/wms.sql
→ 0          （lite 分支）
→ 0          （advance 分支）
```

**两个分支的全部建表语句里，`UNIQUE KEY` 出现 0 次。** 全库唯一性——仓库编码、物料编码、单据号、`(仓库, 规格)` 库存唯一——**全部只靠 Java 应用层「先查再插」保证**。数据库层一道防线都没有。

---

## 二、核心功能

功能清单来自源码与建表语句双向核对，不取自宣传稿。

### 基础资料（`lite` 分支）

| 功能 | 实现 | 关键字段 |
|---|---|---|
| 仓库 | `WarehouseController` / `wms_warehouse` | `warehouse_code, warehouse_name, remark, order_num`。**无「仓库类型」字段** |
| 物料 | `ItemController` / `wms_item` | `item_code, item_name, item_category(字符串), unit, item_brand` |
| 物料分类 | `ItemCategoryController` / `wms_item_category` | `parent_id` 自引用树 |
| 品牌 | `ItemBrandController` / `wms_item_brand` | —— |
| 规格 | `ItemSkuController` / `wms_item_sku` | `length/width/height/gross_weight/net_weight/cost_price/selling_price` |
| 往来单位 | `MerchantController` / `wms_merchant` | 客户／供应商合表，`merchant_type` 区分 |

### 单据与库存

| 功能 | 状态机 | 库存动作 |
|---|---|---|
| 入库 | 暂存 `0` → 完成 `1`；作废 `-1` | 加库存 |
| 出库 | 同上 | 减库存（不足即拦截） |
| 移库 | 同上 | **仓库到仓库**（`source_warehouse_id → target_warehouse_id`），不是库位间 |
| 盘库 | 同上 | 差异直接改写库存 |
| 库存看板 | —— | 分仓库／商品两维度 |
| 库存记录 | —— | `wms_inventory_history` 流水账 |

状态常量定义在 `ruoyi-common-core/.../constant/ServiceConstants.java`：四类单据共用 `PENDING(0) / FINISH(1) / INVALID(-1)`。

### 打印

前端引 `vue-plugin-hiprint 0.0.56`，入库单／出库单支持网页打印。

### 条码与设备：零（事实，已复核）

对 `ruoyi-admin-wms` 全量源码检索 `barcode|条码|PDA|rfid|scan|扫码|设备`——**无一处业务命中**（唯一匹配是 `BusinessType.UPDATE` 里含子串 `PDA` 的假阳性）。前端引了 `jsbarcode` 与 `qrcode`，**只用于展示与打印，没有扫码作业闭环**。

---

## 三、技术栈

### 后端（`pom.xml` 属性块，版本逐项核对）

| 项 | 版本／实现 |
|---|---|
| 语言 | Java 17 |
| 框架 | Spring Boot `3.2.6` |
| 项目版本 | `revision = 5.2.0` |
| 持久层 | MyBatis `3.5.16` + MyBatis-Plus `3.5.6`，`p6spy 3.9.1` |
| **鉴权** | **Sa-Token `1.37.0`**（`sa-token.token-name=Authorization`，`timeout=86400`），**不是 Spring Security** |
| 缓存／锁 | Redis + Redisson `3.29.0` + Lock4j `2.2.7` |
| 多数据源 | dynamic-ds `4.3.0` |
| 接口文档 | SpringDoc `2.5.0` + therapi-javadoc `0.15.0` |
| 导入导出 | POI `5.2.3` + EasyExcel `3.3.4` |
| 代码生成 | Velocity `2.3` |
| 工具 | Hutool `5.8.27`、MapStruct-Plus `1.3.6`、Lombok |
| 存储／短信 | aws-java-sdk-s3 `1.12.540`、sms4j `2.2.0` |
| 加密 | BouncyCastle `1.72`（`ruoyi-common-encrypt`） |
| Web 容器 | Undertow（`io=8 / worker=256`），端口 `8080` |

### 前端（`RuoYi-WMS-VUE/package.json`，`version 4.8.2`）

Vue `3.2.45` · Vite `3.2.3` · Element Plus `2.2.27` · Pinia `2.0.22` · vue-router `4.1.4` · ECharts `5.4.0` · axios `0.27.2` · vue-plugin-hiprint `0.0.56` · jsbarcode `3.11.6` · qrcode `1.5.3` · moment `2.30.1` · jsencrypt `3.3.1`

### 在线体验（三个站点实测均返回 200）

| 地址 | 对应 |
|---|---|
| `https://wms.ichengle.top/` | 仓库说明所载 |
| `http://cangku.ichengle.top/` | 见于第三方转载，对应 `lite` |
| `http://kucun.ichengle.top/` | 见于第三方转载，对应 `advance` |
| `https://docs.ichengle.top/wms/open/run2.html` | 部署文档 |

后两个地址的来源是转载 README 而非本仓库，**标注可信度低于第一个**。

### 文档与实现不符（事实，均已复核）

1. 仓库说明称「后端采用 Spring Boot、**Spring Security**、Redis & Jwt」——`pom.xml` 无 Spring Security 依赖，鉴权实际由 `ruoyi-common-satoken` 承担。
2. `application.yml` 的 Knife4j 分组扫的是 `com.ruoyi.web`，实际业务包是 `com.ruoyi.wms`——**模板残留**。
3. 仓库说明称「仓库/库区/货架管理」——**两分支均无任何货架／库位表**，`lite` 连库区都没有。
4. 仓库说明称 `Merchant` 含「承运商」——字典里只有客户／供应商／客户供应商，**无承运商**。
5. README 徽章标 MIT；`LICENSE` 文件是**改写版 Apache-2.0**；前端 `package.json` 又写 MIT。**三处口径不一**。

---

## 四、整体架构

```
浏览器（Vue 3 + Element Plus SPA，Vite 构建）
        │  HTTP / JSON，Authorization 头携带 Sa-Token
        ▼
ruoyi-admin-wms  ← 唯一可启动的应用（RuoYiApplication）
  controller → service → mapper → resources/mapper/wms/*.xml
        │
        ├── 依赖 ruoyi-common/*（20 个子模块，能力下沉）
        ├── 依赖 ruoyi-modules/ruoyi-system（用户/角色/菜单/字典/OSS/操作日志）
        └── 依赖 ruoyi-modules/ruoyi-generator（代码生成器）
                │
                ▼
        MySQL（lite 35 张表 / advance 37 张表）
        Redis（Sa-Token 会话、缓存、限流、分布式锁、防重提交）
```

| 顶层 | 模块 | 职责 |
|---|---|---|
| `ruoyi-admin-wms` | 单模块，7,707 行 | **仓储业务全部代码** + 启动类 + `application.yml` |
| `ruoyi-common` | 20 个子模块 + `bom` 统一版本 | `core / mybatis / redis / satoken / security / web / log / excel / doc / encrypt / idempotent / json / mail / oss / ratelimiter / sensitive / sms / translation` |
| `ruoyi-modules` | 3 个子模块 | `ruoyi-system`（RBAC 底座）、`ruoyi-generator`、`ruoyi-demo`（示例） |
| `script/sql` | `wms.sql` | 建表 + 菜单 + 字典全套种子数据 |

**架构判断（推论）**：单体 + 能力模块化，不是微服务。业务代码全部堆在一个模块；`service` 层 **17 个类没有接口/实现分离**，直接是 `@Service` 具体类；实体层是三段式（`domain/entity` 17、`domain/bo` 17、`domain/vo` 21）。

---

## 五、模块划分

`lite` 分支 16 个控制器，按域归为六组：

| 域 | 控制器 | 表 |
|---|---|---|
| 基础资料 | `WarehouseController`、`ItemController`、`ItemCategoryController`、`ItemBrandController`、`ItemSkuController`、`MerchantController` | 6 张 |
| 入库 | `ReceiptOrderController`、`ReceiptOrderDetailController` | `wms_receipt_order`、`wms_receipt_order_detail` |
| 出库 | `ShipmentOrderController`、`ShipmentOrderDetailController` | `wms_shipment_order`、`wms_shipment_order_detail` |
| 移库 | `MovementOrderController`、`MovementOrderDetailController` | `wms_movement_order`、`wms_movement_order_detail` |
| 盘库 | `CheckOrderController`、`CheckOrderDetailController` | `wms_check_order`、`wms_check_order_detail` |
| 库存 | `InventoryController`、`InventoryHistoryController` | `wms_inventory`、`wms_inventory_history` |

单据域是**四份高度同构的复制**：主表 + 明细表 + 双控制器 + 双服务 + 双映射器 + 双 XML。加一个新单据域要复制约 12 个文件。

---

## 六、关键业务流程

### 6.1 入库（`lite`：`ReceiptOrderService.receive()`）

```
填写入库单（仓库、入库类型、业务单号、供应商 + 明细）
   │
   ├─ 暂存 insertByBo() → 校验单号唯一 → 写主表+明细（状态 0）
   │
   └─ 确认入库 receive()
        1. 校验明细非空            validateBeforeReceive()
        2. 写/更新入库单与明细      insertByBo() / updateByBo()
        3. 增加库存                inventoryService.add(details)
        4. 写库存流水              saveInventoryHistory(..., RECEIPT, true)
```

`inventoryService.add()`（`InventoryService.java`）：按 `(warehouse_id, sku_id)` 查现有库存 → 存在则记 `beforeQuantity`/`afterQuantity` 累加；不存在则新建、`before = 0`。全程 `@Transactional`。

### 6.2 出库（`lite`：`ShipmentOrderService.shipment()`）

结构与入库镜像对称，第三步换 `inventoryService.subtract()`。**这是 `lite` 分支唯一做了硬性业务校验的地方**：

```java
BigDecimal afterQuantity = beforeQuantity.subtract(bo.getQuantity());
if (afterQuantity.signum() == -1) {
    throw new ServiceException("库存不足", HttpStatus.CONFLICT,
        "…库存不足，当前库存：" + beforeQuantity);
}
```

负库存被显式拦截（HTTP 409）。**加分项。**

### 6.3 移库

`lite` 为**仓库到仓库**调拨。因无库位概念，实质等同两仓调拨。

### 6.4 盘库（`InventoryService.updateInventory()`）

```
明细带 inventoryId → 写入 quantity ≠ 库内实际 → 抛 409「账面库存不匹配」
                  → 相等 → 若 checkQuantity ≠ quantity，直接改写
明细不带 inventoryId → 库内已存在该 (sku, 仓库) → 抛 409；否则新增
```

### 6.5 单据状态机与保护规则

```
PENDING(0) ──确认──▶ FINISH(1)
     └──作废──▶ INVALID(-1)
```

- 已 `FINISH` 的单据**禁止删除**（`validateIdBeforeDelete`，抛 409）；
- **没有红冲／反审核**，已完成的出入库无逆流程；
- **`@RepeatSubmit` 已施加于全部 16 个控制器的写接口**，默认间隔 5000ms（`ruoyi-common-idempotent/.../RepeatSubmit.java`）。这是 Redis 分布式防重，能挡住同一用户的重复点击，**挡不住两个不同用户并发对同一仓库同一规格操作**。

### 6.6 库存流水（全项目最有价值的一张表）

`wms_inventory_history` 字段：
`warehouse_id, sku_id, quantity, before_quantity, after_quantity, amount, order_id, order_no, order_type, create_time`

`order_type`：`1 入库 / 2 出库 / 3 移库 / 4 盘库`。

每次库存变更留下「变更前 + 变更后 + 来源单据」，**可审计、可回溯**。这是它区别于一般「库存增删改查玩具」的核心资产。

---

## 七、模块间依赖关系

### 业务服务层真实依赖图（读源码得出）

```
ReceiptOrderService ───┬─▶ ReceiptOrderDetailService
                       ├─▶ InventoryService ──▶ ItemSkuService
                       └─▶ InventoryHistoryService

ShipmentOrderService ──┼─▶ ShipmentOrderDetailService
                       ├─▶ InventoryService
                       └─▶ InventoryHistoryService

MovementOrderService ──┼─▶ MovementOrderDetailService
                       ├─▶ InventoryService
                       └─▶ InventoryHistoryService

CheckOrderService ─────┼─▶ CheckOrderDetailService
                       ├─▶ InventoryService
                       └─▶ InventoryHistoryService
```

**结构判定（推论）**：`InventoryService` 是唯一的业务汇聚点，四类单据全部依赖它收口库存变更，**避免了口径分裂，设计上这是对的**。副作用是它同时承担「库存读写」「盘库校验」「并发控制」三件事。

### 跨层依赖

- 业务服务依赖 `ruoyi-common-*`（`common-core` 的异常与工具、`common-mybatis` 的 `BaseEntity`/`PageQuery`/`TableDataInfo`）。
- 控制器依赖 `ruoyi-common-web`（统一响应、全局异常）、`ruoyi-common-satoken`（`@SaCheckPermission`）。
- 依赖方向单向：`ruoyi-admin-wms → ruoyi-modules → ruoyi-common`，`ruoyi-common` 不反向依赖业务，**无循环依赖**。
- **四个业务域之间零依赖**，只通过 `InventoryService` 交互。既是优点（解耦），也是缺陷——**无法串接跨域流程**（例如「入库后自动生成上架任务」没有落点）。

### 一处分层破坏（事实）

`advance` 分支的三个控制器**直接编排数据清理**：

- `ShipmentOrderController.java:108` → `inventoryDetailService.clearDataWithZeroRemainQuantity();`
- `CheckOrderController.java:109` → 同上
- `MovementOrderController.java:109` → 同上

业务收尾逻辑写在控制器里，且**在业务事务之外**（见 P4）。

---

## 八、`advance` 分支专项：库区、批次、效期

`advance` 比 `lite` 多两张表、多一个控制器域：

| 维度 | `lite`（= `master`） | `advance` |
|---|---|---|
| 库区 | **无** | `wms_area`（`area_code, area_name, warehouse_id`）+ `AreaController` |
| 批次／效期 | **无** | `batch_no / production_date / expiration_date` 贯穿 entity／bo／vo |
| 库存明细 | **无** | `wms_inventory_detail`（含 `remain_quantity` 剩余量） |
| 一物一码 | 无 | 有 `sn` 口径 |
| 表数 | 35 | 37 |

### 关键结论：有批次字段，**没有先进先出，也没有效期管控**（事实）

**依据一：出库批次由用户手工指定，系统不自动分配。**
`advance/ShipmentOrderService.convertShipmentOrderDetailToInventoryDetail()`：

```java
inventoryDetailBo.setId(detail.getInventoryDetailId());   // 直接用前端传来的明细行 ID
inventoryDetailBo.setShipmentQuantity(detail.getQuantity());
```

**依据二：扣减 SQL 无任何排序或分配策略。**
`advance/.../mapper/wms/InventoryDetailMapper.xml:16` 的 `deductInventoryDetailQuantity` 是按传入 `id` 列表逐行扣减，**没有 `ORDER BY expiration_date`**。全仓 `mapper/wms/*.xml` 里的 `order by` 全是**展示排序**（`warehouse_id, area_id, item_id, create_time`），不是分配策略。

**依据三：无效期拦截。**
`InventoryDetailService.queryPageList()` 里的 `expirationStartTime.plusDays(bo.getDaysToExpires())` 是**查询「N 天内将到期」的筛选区间**，用于列表展示。service 层**没有任何** `isBefore` / `isAfter` 形式的效期比较——**「已过期的批次仍可正常出库」**，系统不拦。

**依据四：两支都没有乐观锁实体。**
`grep -rn "@Version"` 全仓仅命中 `ruoyi-demo` 的两个示例实体（`TestDemo.java:57`、`TestTree.java:49`），**业务实体一个都没有**。

### 结论

`advance` 的批次与效期是**「记录级」而非「管控级」**：字段落库、能查、能筛，但**不参与作业决策**。若需要「先到期先出」或「过期禁出」，得自行开发。

---

## 九、适用场景与亮点

### 适用场景（**标注为猜测**，依据是功能集规模与缺失项推断，不是我从源码读出的客户画像）

**适合**：
1. 单一企业自营仓库的库存台账——需求止步于「账实相符 + 单据打印」。
2. 需要快速二开的**项目底座**：代码生成器 + 约 20 个开箱即用的框架能力模块。
3. 学习若依生态的样本（JDK 17 + Spring Boot 3 + Vue 3 + Element Plus）。
4. **不需要库位精细化**的场景——只要知道「货在哪个仓、有多少」。

**不适合**（这一组是**事实推论**，依据是数据结构与代码缺失）：
1. **三方云仓 / 一仓多货主**——库存无货主维度（第一节）。
2. **库位级作业**——无库位表、无上架／拣货／波次／路径。`advance` 最细到「库区」。
3. **批次／效期强管控**——`lite` 无字段；`advance` 有字段但**无先进先出、无效期拦截**（第八节）。
4. **条码／手持终端作业**——全项目零条码、零设备接口。
5. **多租户**——许可证明文限制（见第十节）。

### 亮点

**属于这个项目本身的**：
1. **库存流水账完整**——`wms_inventory_history` 的「变更前 + 变更后 + 来源单据」三件套，让库存可审计。多数同类开源只写结果不写过程。
2. **`InventoryService` 单点收口**——四类单据共用一套库存变更逻辑，口径不分裂。
3. **负库存硬拦截**——出库显式校验并抛 409，不是靠前端限制。
4. **已完单禁删**——`FINISH` 状态禁止删除，防「删了单据但库存没回退」的数据不一致。
5. **写接口统一防重**——16 个控制器全部施加 `@RepeatSubmit`。

**属于选型收益、不是本项目功劳的**（上一版我曾把这两条错记成项目亮点，此处更正）：若依系 `ruoyi-common` 的 20 个能力模块（加解密、脱敏、幂等、限流、多数据源、对象存储、短信、国际化），以及代码生成器——**这些来自 `ruoyi-vue-fast` 底座**。

---

## 十、潜在问题（按致命 → 严重 → 一般排序，**每条给改进方向与红队对立方案**）

### 致命级

**P1 · 库存在模型层无法表达货权分离**
`wms_inventory` 主键仅 `(sku_id, warehouse_id)`，无货主／批次／库位／库存状态。一切「同规格不同归属」装不下。
- **改进**：主键扩为 `(货主, 仓库, 库位, 规格, 批次, 库存状态)`，并引入「可用量／占用量／冻结量」三量分离。
- **对立方案**：不改主键，另建「货权分摊子表」（`wms_inventory_owner`）按比例分摊数量。**适用条件**：货主粒度只用于对账展示、不需要按货主独立执行出库与库位分配。**若需按货主独立拣货，此方案立刻失效。**

**P2 · 无自动化设备接口层**
定位为人工 + 手持终端，但**代码里连条码都零出现**，更无设备接口抽象。要对接立库、电子标签、分拣线等于从零加一层。
- **改进**：抽出「作业指令」抽象层，把手持终端与自动化设备统一为指令下发／回执。
- **对立方案**：按设备逐个硬编码适配器。**适用条件**：设备种类少于两种且不打算换品牌。**超过两种，适配器会互相污染。**

### 严重级

**P3 · 乐观锁插件形同虚设，并发下库存会算错（本次已从推论升级为事实）**

上一版我把这条标为「推论，接受降级」，理由是「未读 `ruoyi-common-mybatis` 是否全局开了乐观锁」。**现在读了，结论比上一版更糟：**

- `ruoyi-common-mybatis/.../MybatisPlusConfig.java:31-38` **确实注册了** `OptimisticLockerInnerInterceptor`（注释写明「乐观锁插件」）；
- `grep -rn "@Version"` 全仓仅命中 `ruoyi-demo` 的两个**示例**实体；
- **业务实体一个 `@Version` 都没有** → 拦截器对库存、单据**完全不生效**；
- `InventoryService.add() / subtract() / updateInventory()` 均为「查询 - 判断 - 写入」，**无锁、无版本号**。

**后果**：两个用户并发对同一仓库同一规格出库，各自 `selectOne` 读到同一个旧值，各自通过 `afterQuantity.signum() != -1` 校验，各自 `updateBatchById` 覆盖——**库存可被写成负数，且两条流水都显示成功**。`@RepeatSubmit` 只挡同一用户的 5 秒内重复点击，挡不住这个。

- **改进**：库存表加 `version` 字段并在实体打 `@Version`（插件已就位，改造成本极低）；或对 `(warehouse, sku)` 加 Redisson 分段锁。
- **对立方案**：不改代码，把库存变更串行化进单线程队列。**适用条件**：单仓单规格写入频次极低。**频次一上来，队列会成为瓶颈与单点。**

**P4 · 全库零唯一约束（本次已从「一般级」升级）**

上一版我写的是「`wms_inventory` 未见唯一索引」。**实际是更彻底的问题**：

```
grep -c "UNIQUE KEY" script/sql/wms.sql  →  0   （lite）
                                         →  0   （advance）
```

**两个分支、37 张表，全部建表语句里 `UNIQUE KEY` 出现 0 次。** 单据号唯一靠 `validateXxxOrderNo()`「先查再插」（`ReceiptOrderService`、`ShipmentOrderService`、`MovementOrderService` 各写一份），仓库编码、物料编码、`(仓库, 规格)` 库存唯一**全部无数据库层保障**。并发下「先查再插」可插出重复行；`selectOne` 遇多行直接抛异常。

- **改进**：至少给 `wms_inventory(sku_id, warehouse_id)`、各单据 `order_no`、`warehouse_code`、`item_code` 补唯一索引。
- **对立方案**：不加约束，把 `selectOne` 全改 `selectList` 后合并。**适用条件**：能接受库存行冗余与后续对账成本。**不推荐——这是把问题往后推。**

**P5 · `advance` 的零剩余批次行被「全表清扫」删除，且写在控制器里、事务之外（本次新发现）**

`advance/InventoryDetailService.java:143`：

```java
public void clearDataWithZeroRemainQuantity() {
    LambdaQueryWrapper<InventoryDetail> wrapper = Wrappers.lambdaQuery();
    wrapper.eq(InventoryDetail::getRemainQuantity, 0);   // ← 无任何其他条件
    inventoryDetailMapper.delete(wrapper);
}
```

调用处（`ShipmentOrderController.java:108`、`CheckOrderController.java:109`、`MovementOrderController.java:109`）：

```java
shipmentOrderService.shipment(bo);
inventoryDetailService.clearDataWithZeroRemainQuantity();   // ← 在 shipment 事务之外
```

三重问题：
1. **跨仓误伤**——查询条件只有 `remain_quantity = 0`，**没有限定仓库／商品／单据**。A 仓出库会删掉全库所有零剩余批次行，包括 B 仓的。
2. **事务边界错误**——`shipment()` 自带 `@Transactional`，控制器不在事务内，清理是**独立事务**。出库成功而清理失败则残留；清理成功而出库回滚则数据提前丢失。
3. **溯源断裂**——批次库存行被**物理删除**，批次追溯只能改从 `wms_inventory_history` 反查。而 `inventory_detail` 本是记录「哪张入库单、哪个批次、还剩多少」的表，删掉即失去「批次 → 入库单」的直接链路。

- **改进**：加 `warehouse_id`／`sku_id` 限定；移入 `shipment()` 的同一事务；改物理删除为软删或归档。
- **对立方案**：不清理，让零剩余行留在表里。**适用条件**：表数据量可控。**这是最安全的做法——清理不是功能，是优化，优化不该带正确性风险。**

### 一般级

**P6 · 四套单据代码同构复制，未抽象**
实体层已有 `BaseOrder`/`BaseOrderDetail`/`BaseOrderBo`/`BaseOrderDetailBo`，但**控制器与服务未抽象**，四域各自一套。
- **改进**：推为泛型基类 + 策略。
- **对立方案**：不做抽象，靠代码生成器保证四份一致。**适用条件**：单据域不再增加且团队接受「模板改动需同步 regenerate」。**生成器不校验历史数据，一致性靠人，长期会漂移。**

**P7 · `wms_item.item_category` 是字符串而非外键**
存的是分类**名称**（`varchar(20)`），不是 `wms_item_category.id`。分类改名或删除会让物料分类悬空。
- **改进**：改为 `category_id bigint` 外键。
- **对立方案**：保留字符串，禁止分类改名与删除。**适用条件**：分类一次性定型且永不变更——现实里几乎不成立。

**P8 · 配置残留与文档失实**
见第三节末列出的 5 条（Spring Security／`com.ruoyi.web`／货架／承运商／许可证口径）。**建议以代码为准重写文档**；若对外分发，文档失实是事故。

### 许可证（单列，对商用是硬约束）

`LICENSE` 原文（改写版 Apache-2.0，**照录关键条款**）：

> 1. …Should the conditions below be met, a commercial license must be obtained from the producer:
>    a. **Multi-tenant service**: Unless explicitly authorized by ruoyi-wms in writing, you may not use the ruoyi-wms source code to operate a multi-tenant environment.
>    b. **LOGO and copyright information**: …you may not remove or **moruoyi-wms** the LOGO or copyright information…
>
> …The interactive design of this product is protected by appearance patent.

（原文 1.b 中「moruoyi-wms」是**作者笔误**，应为「modify」。我照录不擅改。）

**三条要点**：① 不得用于多租户（除非书面授权）；② 不得移除 LOGO 与版权；③ 交互设计受外观设计专利保护。

**对本项目的直接冲突**：「一仓 N 货主」正是多租户形态。**这不是可以事后处理的技术债，是必须先过的法务门。**

另：gitcc 改名打包分发，**若未保留版权与许可文件，本身就落在第 1.b 条上**——但**我没看到它的源码，无法确认**，这只是条件陈述。

---

## 反方审查

**1. 「你这整篇分析的不是用户要的那个项目。」**
**成立。** 原地址不可读，我分析的是上游真身。辩护只有一条且诚实：两者描述文本逐字重合、功能清单一对应，**若 gitcc 版有独有功能，我会漏掉**。这条反驳不了，接受。

**2. 「P3 并发问题是你搭的稻草人，乐观锁插件都注册了。」**
**上一版我接受降级；这一版我推翻自己。** 读了源码后：插件确实注册，**但零业务实体带 `@Version`，拦截器不生效**，所以并发缺陷成立，且是事实级。**这里我要说清一件上一版说错的事**：上一版我写「未读 `ruoyi-common-mybatis`，故降级为推论」——降级本身是对的，但我当时把这个不确定性表述得像是「可能已缓解」。**实际读了才知道是「已注册但未启用」，比「没注册」更隐蔽——它给人已防护的错觉。** 这条我维持升级后的判断。

**3. 「P5 那条『全表清扫』是不是你把 `@Transactional` 边界看错了？」**
**我不认为看错，但承认有半条没验。** 我确认了：`clearDataWithZeroRemainQuantity()` 的 wrapper 只有 `remain_quantity = 0` 一个条件（源码照录）；控制器未标 `@Transactional`，`shipment()` 自带 `@Transactional`，默认传播下 `shipment()` 返回即提交，故清理在独立事务——这条成立。**但我没跑起来实测「A 仓出库是否真的删了 B 仓的行」**，也没有 `advance` 分支的运行时数据。所以：**代码逻辑是事实，运行后果是推论。** 这半条我标清楚。

**4. 「适用场景那一节你又在编客户画像。」**
**上一版我认了这个错，这次已改口径**：整节标注为**猜测**，并明确写「依据是功能集规模与缺失项推断，不是从源码读出的客户画像」。但「不适合」那一组我维持为**事实推论**——依据是数据结构与代码缺失（库存无货主列、无库位表、无条码），不是行业印象。

**5. 「亮点里你把若依框架的能力算成项目亮点。」**
**上一版已认账并改口径**，本次进一步拆成两栏：「属于这个项目本身的」与「属于选型收益的」。真正属于项目的只有 5 条。

**6. 「P5 说物理删除导致溯源断裂——可 `wms_inventory_history` 不就是干这个的吗？」**
**这条我反驳不了，接受修正。** 溯源能力本身没丢，`wms_inventory_history` 记录了每次变更。**准确的说法应该是**：丢失的是「批次行 → 原始入库单」的**直接关联**（`wms_inventory_detail.receipt_order_id`），改由流水间接反查，链路变长、且需要流水完整无缺口。我已按此修正 P5 第 3 点。

**7. 「既然原地址不可读，你为什么不等用户确认就直接分析上游？」**
**接受。** 这是流程越权，不是内容错误。上一版已认，本次未重犯——本次是你说「若依 WMS 找这个」之后才动手的。

---

## 未决项

**本次已关闭两条：**

| 编号 | 原未决项 | 结论 |
|---|---|---|
| 原 3 | `advance` 的批次／效期／先进先出是否落到业务层 | **已关闭**。有字段、无先进先出、有效期筛选、**无效期拦截**；批次由用户手工指定。见第八节 |
| 原 4 | `ruoyi-common-mybatis` 是否启用乐观锁 | **已关闭**。插件已注册，**零业务实体带 `@Version`，不生效**。见 P3 |

**仍然未决：**

1. **gitcc 版与上游是否完全一致——我判断不了。** 需你提供可读源码（压缩包／镜像／登录后页面）。
2. **`gibbon-wms` 与 `gibbon-wms-plat` 是两个项目还是一套的两支——我判断不了。** 前者完全空白。
3. **P5「跨仓误伤」的运行后果未经实测**——代码逻辑已确认，运行时行为是推论。需在 `advance` 环境上验证。
4. **许可证「多租户」的定义边界——需法务判断。** 「一仓 N 货主、货权分离但同属一个签约主体」算不算，我做不了这个判断。
5. **gitcc 是否需付费、注册是否开放——我判断不了。** `sign_in` 由 JS 客户端渲染，抓不到结构。
6. **要不要做一次「若依 WMS → 三方云仓」的改造差距评估——我没做。** 那是独立任务，本次未展开。
