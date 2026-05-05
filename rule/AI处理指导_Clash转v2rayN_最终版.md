# Clash rules.yml → v2rayN 路由规则转换 · AI 处理指导手册（最终版）

> 本文档专为 AI 提供处理指导，包含完整规则、验证逻辑和可直接运行的代码。  
> 适用版本：v2rayN v7.21 · Xray 26.x  
> 版本：v3.0 · 2026-05-05（合并两份文档优点，修复所有已知错误）

---

## 〇、TL;DR — 最终有效方案

```
保留：DOMAIN → full:   DOMAIN-SUFFIX → domain:   IP-CIDR/IP-CIDR6 → ip[]   DST-PORT → port
删除：DOMAIN-KEYWORD（全部）   GEOIP（全部）   MATCH（忽略）
ip 字段：每条 CIDR 独立数组元素，绝不 \n 拼接
domain 字段：每条独立数组元素
```

---

## 一、给 AI 的指令模板

下次直接将此模板 + clash.yml + 本文档一起发给 AI：

```
请将我上传的 clash.yml 转换为 v2rayN 可导入的路由规则 JSON 文件。
转换规范请严格遵照本文档第二节至第五节执行，不要自行发挥。
输入路径：/mnt/user-data/uploads/clash.yml
输出路径：/mnt/user-data/outputs/v2rayn_routing_rules.json
```

---

## 二、输入格式（Clash rules.yml）

```yaml
rules:
  - DOMAIN,google.com,🔰 选择节点
  - DOMAIN-SUFFIX,youtube.com,🔰 选择节点
  - DOMAIN-KEYWORD,steam,🔰 选择节点      # ← 必须删除
  - IP-CIDR,8.8.8.8/32,🔰 选择节点,no-resolve
  - IP-CIDR6,2001:4860::/32,🔰 选择节点
  - GEOIP,CN,🇨🇳 国内网站                  # ← 必须删除
  - DST-PORT,25,DIRECT
  - MATCH,🔰 选择节点                       # ← 忽略
```

---

## 三、输出格式（v2rayN 导入 JSON）

```json
[
  {
    "port": "",
    "outboundTag": "proxy",
    "domain": [
      "full:google.com",
      "domain:youtube.com"
    ],
    "ip": [
      "8.8.8.8/32",
      "2001:4860::/32"
    ],
    "enabled": true,
    "remarks": "选择节点"
  },
  {
    "port": "25,110,143",
    "outboundTag": "direct",
    "domain": [],
    "ip": [],
    "enabled": true,
    "remarks": "邮件端口直连"
  }
]
```

### 关键字段规则

| 字段 | 规则 | 错误示例 | 正确示例 |
|------|------|----------|----------|
| `domain` | 每条独立数组元素 | — | `["full:a.com", "domain:b.com"]` |
| `ip` | **每条必须独立**，绝不 `\n` 拼接 | `["8.8.8.8/32\n1.1.1.0/24"]` ❌ | `["8.8.8.8/32", "1.1.1.0/24"]` ✅ |
| `port` | 多端口用英文逗号分隔 | — | `"25,110,143,465"` |
| `outboundTag` | 仅使用 `proxy` / `direct` / `block`，全小写 | `"PROXY"` ❌ | `"proxy"` ✅ |

---

## 四、规则类型映射

| Clash 规则类型 | 处理方式 | v2rayN 格式 | 原因 |
|--------------|----------|-------------|------|
| `DOMAIN` | ✅ 保留 | `"full:xxx"` | 精确匹配完整域名 |
| `DOMAIN-SUFFIX` | ✅ 保留 | `"domain:xxx"` | 后缀+子域名匹配 |
| `DOMAIN-KEYWORD` | ❌ **全部删除** | — | Xray 26.x 对 keyword 值执行 LDH 校验，含 `-spotify-` 等连字符的合法 Clash keyword 会导致 Core 启动失败，且改用 `regexp:` 也无法规避 |
| `IP-CIDR` | ✅ 保留 | `ip[]` 独立元素 | 去掉尾部 `no-resolve` 标记 |
| `IP-CIDR6` | ✅ 保留 | `ip[]` 独立元素 | 同上 |
| `GEOIP` | ❌ **全部删除** | — | 引发额外配置问题，改用具体 CIDR 替代 |
| `DST-PORT` | ✅ 保留 | `port` 字段 | 同策略组多端口逗号拼接 |
| `MATCH` | 忽略 | — | v2rayN 有独立兜底机制 |

---

## 五、outboundTag 映射

```
DIRECT                → "direct"
REJECT                → "block"
🔰 选择节点            → "proxy"
🌏 爱奇艺&哔哩哔哩      → "proxy"
📺 动画疯              → "proxy"
🎮 Steam 登录/下载     → "direct"   # CDN 直连
🎮 Steam 商店/社区     → "proxy"
☁️ OneDrive           → "proxy"
🎓 学术网站            → "proxy"    # ⚠️ 必须是 proxy：学术网站在大陆均被封锁
🇨🇳 国内网站           → "direct"
🌩️ Cloudflare        → "proxy"
🛑 拦截广告            → "block"
🐟 漏网之鱼            → "proxy"
```

> **未列出的策略组默认映射为 `"proxy"`**

---

## 六、完整处理代码

```python
import json, re
from collections import defaultdict, OrderedDict

# ── outboundTag 映射 ──────────────────────────────────────────────
ACTION_META = {
    'DIRECT':             ('direct', 'DIRECT直连'),
    'REJECT':             ('block',  'REJECT拦截'),
    '🔰 选择节点':         ('proxy',  '选择节点'),
    '🌏 爱奇艺&哔哩哔哩':  ('proxy',  '爱奇艺哔哩哔哩'),
    '📺 动画疯':           ('proxy',  '动画疯'),
    '🎮 Steam 登录/下载':  ('direct', 'Steam登录下载'),
    '🎮 Steam 商店/社区':  ('proxy',  'Steam商店社区'),
    '☁️ OneDrive':        ('proxy',  'OneDrive'),
    '🎓学术网站':          ('proxy',  '学术网站'),   # proxy，非 direct
    '🇨🇳 国内网站':        ('direct', '国内网站'),
    '🌩️ Cloudflare':     ('proxy',  'Cloudflare'),
    '🛑 拦截广告':         ('block',  '拦截广告'),
    '🐟 漏网之鱼':         ('proxy',  '漏网之鱼'),
}

# ── LDH 域名合法性校验 ────────────────────────────────────────────
LABEL_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?$')

def is_valid_domain_entry(entry: str) -> bool:
    """
    严格 LDH 校验：每个 label 只含 [a-zA-Z0-9-]，
    且不以连字符开头或结尾，全域名必须含至少一个点，纯 ASCII。
    """
    if entry.startswith('full:'):
        val = entry[5:]
    elif entry.startswith('domain:'):
        val = entry[7:]
    else:
        return False
    if not val.isascii():      return False  # 非 ASCII
    if '.' not in val:         return False  # 单级域名（无点）
    for label in val.split('.'):
        if not label:          return False  # 空 label（连续点/首尾点）
        if not LABEL_RE.match(label): return False
    return True

# ── 主转换函数 ────────────────────────────────────────────────────
def convert_clash_to_v2rayn(rules_yml_path: str) -> list:
    # 用 OrderedDict 保持策略组出现顺序，避免规则优先级错位
    by_action = OrderedDict()

    def ensure(action):
        if action not in by_action:
            by_action[action] = {'domain': [], 'ip': [], 'port': []}

    with open(rules_yml_path, 'r', encoding='utf-8') as f:
        in_rules = False
        for line in f:
            stripped = line.strip()

            # 自动定位 rules: 块，不依赖固定行号
            if stripped == 'rules:':
                in_rules = True
                continue
            if not in_rules:
                continue
            # rules 块结束（遇到顶级 key）
            if stripped and not stripped.startswith('-') and stripped.endswith(':'):
                break

            if not stripped.startswith('- '):
                continue
            parts = stripped[2:].split(',')
            if len(parts) < 2:
                continue

            rule_type = parts[0].strip().upper()
            value     = parts[1].strip()
            action    = parts[2].strip() if len(parts) >= 3 else 'MATCH'

            if rule_type == 'DOMAIN':
                ensure(action)
                by_action[action]['domain'].append(f'full:{value}')

            elif rule_type == 'DOMAIN-SUFFIX':
                ensure(action)
                by_action[action]['domain'].append(f'domain:{value}')

            elif rule_type == 'DOMAIN-KEYWORD':
                pass   # 全部丢弃：Xray 26.x LDH 不兼容

            elif rule_type in ('IP-CIDR', 'IP-CIDR6'):
                ensure(action)
                by_action[action]['ip'].append(value)  # 独立元素，绝不 \n 拼接

            elif rule_type == 'DST-PORT':
                ensure(action)
                by_action[action]['port'].append(value)

            elif rule_type == 'GEOIP':
                pass   # 全部丢弃

            # MATCH 直接忽略

    result = []
    for action, data in by_action.items():
        if action == 'MATCH':
            continue

        tag, remarks = ACTION_META.get(action, ('proxy', action))

        # 过滤非法域名（LDH 校验）
        clean_domains = [d for d in data['domain'] if is_valid_domain_entry(d)]

        ip_list   = data['ip']
        port_list = data['port']

        # 跳过空规则
        if not clean_domains and not ip_list and not port_list:
            continue

        result.append({
            "port":        ','.join(port_list) if port_list else "",
            "outboundTag": tag,
            "domain":      clean_domains,   # 每条独立
            "ip":          ip_list,         # 每条独立，绝不 \n 拼接
            "enabled":     True,
            "remarks":     remarks,
        })

    return result


# ── 入口 ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    inp = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/clash.yml'
    out = sys.argv[2] if len(sys.argv) > 2 else '/mnt/user-data/outputs/v2rayn_routing_rules.json'

    rules = convert_clash_to_v2rayn(inp)

    with open(out, 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    print(f'✅ 生成 {len(rules)} 条规则组 → {out}')
    for r in rules:
        print(f"  [{r['outboundTag']:6s}] {r['remarks']:20s}"
              f"  domain={len(r['domain'])}  ip={len(r['ip'])}  port={r['port'] or '-'}")
```

---

## 七、v2rayN v7.21 设置 block 出站

> ⚠️ **block 出站不是内置的，必须手动添加，否则拦截规则报错。**

### 正确入口

```
菜单栏「配置项」→「添加自定义配置」
```

### 操作步骤

1. 将以下 JSON 保存为本地文件，例如 `block_outbound.json`：

```json
{
  "outbounds": [
    {
      "tag": "block",
      "protocol": "blackhole",
      "settings": {
        "response": {
          "type": "none"
        }
      }
    }
  ]
}
```

2. 点击顶部菜单**「配置项」** → **「添加自定义配置」**
3. 在「地址 (address)」栏点击**「浏览」**，选择上方保存的 `block_outbound.json`
4. 填写别名（如 `block出站`），点击**「确定」**
5. 点击「重启服务」
6. 验证：`Ctrl+L` 打开日志，出现 `[socks -> block]` 即生效

### ❌ 不要使用「完整配置模板设置」

启用完整配置模板后，v2rayN 会忽略路由设置界面的所有规则，导致路由配置全部失效。

---

## 八、常见错误速查

| 错误信息 | 根本原因 | 解决方案 |
|---------|---------|---------|
| `illegal ip rule: x.x.x.x\ny.y.y.y` | ip 字段用 `\n` 拼接多条 | 每条 CIDR 独立数组元素 |
| `pattern string does not conform to Letter-Digit-Hyphen (LDH) subset` | domain 含非法条目 或 存在 keyword 条目 | 运行 `is_valid_domain_entry()` 过滤；删除所有 DOMAIN-KEYWORD |
| `invalid CIDR prefix length` | ip 字段含 `\n` 拼接 | 同上，每条独立 |
| 启动成功但网络全断 | 规则覆盖过广 | 检查 DIRECT 规则是否正确，确认 outboundTag 拼写 |
| 拦截广告无效 | block 出站未添加 | 按第七节添加自定义配置 |

---

## 九、验证清单（AI 输出前自查）

- [ ] `ip` 字段：每条 CIDR 是独立数组字符串，无 `\n`
- [ ] `domain` 字段：无 DOMAIN-KEYWORD 转来的条目
- [ ] `domain` 字段：所有条目通过 `is_valid_domain_entry()` 校验
- [ ] `outboundTag`：仅使用 `proxy` / `direct` / `block`，全小写
- [ ] 无 `geoip:` 前缀的 ip 条目
- [ ] 纯 IP 或纯 Port 的策略组未被跳过（脚本遍历 `by_action`，不存在此风险）
- [ ] 空规则（domain/ip/port 均为空）已跳过
- [ ] 学术网站 outboundTag 为 `proxy`，非 `direct`
