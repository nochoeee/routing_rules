# Clash → v2rayN 路由规则转换解决方案

> 适用版本：v2rayN v7.x · Xray 26.x · Windows

---

## 一、问题根源总结

将 Clash 的 `rules.yml` 转换为 v2rayN 路由规则时，先后遇到三类错误，根本原因是 **Xray 26.x 对路由规则字段执行严格的 LDH（Letter-Digit-Hyphen）语法校验**，而 Clash 的规则格式并不遵守这套标准。

---

## 二、三类错误详解

### 错误 1：IP 字段用 `\n` 拼接

**错误现象**
```
illegal ip rule: 45.43.32.234/32\n103.151.150.0/23\n...
invalid CIDR prefix length: 32\n103.151.150.0
```

**原因**  
参考 v2rayN 导出文件格式时误以为 `domain` 和 `ip` 字段规则一致，将多个 IP 用 `\n` 拼成一个字符串放入数组。实际上：

| 字段 | 是否支持 `\n` 拼接 |
|---|---|
| `domain` | ✅ 支持，v2rayN 会按 `\n` 拆分 |
| `ip` | ❌ 不支持，每条 CIDR 必须是独立数组元素 |

**正确格式**
```json
{
  "domain": ["full:google.com\ndomain:youtube.com"],
  "ip": ["8.8.8.8/32", "1.1.1.1/32"]
}
```

---

### 错误 2：`domain` / `full` 字段含非法域名

**错误现象**
```
pattern string does not conform to Letter-Digit-Hyphen (LDH) subset
```

**原因**  
Clash 规则中存在不符合 DNS LDH 规范的域名条目，Xray 解析时直接报错退出。

**常见非法条目类型**

| 类型 | 示例 | 原因 |
|---|---|---|
| 单级 TLD | `domain:cn` `domain:hk` `domain:eu` | 不含 `.`，非合法域名 |
| label 首尾有连字符 | `domain:fc-.cdn.bcebos.com` | `fc-` 违反 LDH 规范 |
| punycode 裸 TLD | `domain:xn--fiqs8s` | 无二级域名部分 |
| 占位符 | `domain:gfwlist.start` `domain:gfwlist.end` | 规则文件元数据，非真实域名 |
| 空 label | `domain:.example.com` | 连续点或首尾点 |

**LDH 规范（每个 label 必须满足）**
```
^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?$
```
即：只含字母/数字/连字符，且不以连字符开头或结尾。

---

### 错误 3：`keyword:` 在 Xray 26.x 中触发 LDH 校验

**错误现象**  
同上：`pattern string does not conform to Letter-Digit-Hyphen (LDH) subset`

**原因**  
Xray 26.x 版本对 `keyword:` 类型的值**也执行 LDH 校验**（旧版本不校验）。  
Clash 中的部分关键词含有首尾连字符，例如：

```
keyword:-spotify-
keyword:apiproxy-device-prod-nlb-
keyword:dualstack.apiproxy-
keyword:nikke-
keyword:.
```

这些在 Clash 中完全合法，但 Xray 26.x 解析时报错。

**尝试过但无效的方案**  
将 `keyword:` 改为 `regexp:` 格式：
```
regexp:\-spotify\-
```
理论上 `regexp:` 不经过 LDH 校验，但实测 v2rayN 在转换成 Xray config 时仍然触发了同样错误，原因是 v2rayN 内部处理流程的问题。

**最终有效方案：删除全部 keyword 条目**

---

## 三、最终解决方案

### 转换规则

| Clash 规则类型 | 处理方式 | 原因 |
|---|---|---|
| `DOMAIN` | 转为 `full:xxx`，每条独立数组元素 | ✅ 完全支持 |
| `DOMAIN-SUFFIX` | 转为 `domain:xxx`，每条独立数组元素 | ✅ 完全支持 |
| `DOMAIN-KEYWORD` | **全部删除** | ❌ Xray 26.x 校验不通过 |
| `IP-CIDR` / `IP-CIDR6` | 直接写入 `ip` 字段，每条独立 | ✅ 完全支持 |
| `GEOIP` | **删除**，用具体 CIDR 替代 | ⚠️ 可能引发额外问题 |
| `DST-PORT` | 写入 `port` 字段，逗号分隔 | ✅ 完全支持 |
| `MATCH` | 不转换（v2rayN 有兜底机制） | — |

### 域名过滤规则（Python 验证函数）

```python
import re

def is_valid_domain_entry(entry: str) -> bool:
    prefix = 'full:' if entry.startswith('full:') else 'domain:'
    val = entry[len(prefix):]
    
    # 必须是纯 ASCII
    if not val.isascii():
        return False
    # 必须含至少一个点
    if '.' not in val:
        return False
    # 每个 label 严格校验
    for label in val.split('.'):
        if not label:
            return False  # 空 label（连续点或首尾点）
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?$', label):
            return False  # 含非法字符或首尾连字符
    return True
```

### 正确的 JSON 结构

```json
[
  {
    "port": "",
    "outboundTag": "proxy",
    "domain": [
      "full:google.com",
      "domain:youtube.com",
      "domain:github.com"
    ],
    "ip": [
      "8.8.8.8/32",
      "1.1.1.0/24"
    ],
    "enabled": true,
    "remarks": "选择节点"
  },
  {
    "port": "25,110,143,465,587,993,995",
    "outboundTag": "direct",
    "domain": [],
    "ip": [],
    "enabled": true,
    "remarks": "邮件端口直连"
  }
]
```

---

## 四、outboundTag 对照

| Clash 策略 | v2rayN outboundTag |
|---|---|
| `DIRECT` | `direct` |
| `REJECT` | `block` |
| 代理节点（选择节点等） | `proxy` |

> `block` 出站需要在 v2rayN 出站设置中手动添加一个类型为"黑洞（Blackhole）"的出站，tag 命名为 `block`。

---

## 五、下次转换操作清单

- [ ] `domain` 字段：每条独立数组元素，不使用 `\n` 拼接  
- [ ] `ip` 字段：每条独立数组元素，**绝对不能** `\n` 拼接  
- [ ] 删除所有 `DOMAIN-KEYWORD` 条目  
- [ ] 删除所有 `GEOIP` 条目（或只保留 `geoip:cn` 等已确认可用的）  
- [ ] 过滤所有不含 `.` 的 domain/full 条目  
- [ ] 过滤所有 label 首尾有连字符的域名  
- [ ] 过滤所有含非 ASCII 字符的域名  
- [ ] 导入前在 v2rayN 中**清空现有路由规则**，避免旧规则残留冲突  

---

## 六、已知损失

删除 keyword 规则后，以下匹配功能失效（影响较小）：

- 含 `google` 关键词的未知子域名
- 含 `steam` 关键词的域名
- 含 `spotify` 关键词的域名
- 等约 100 条关键词规则

如需补充，建议在 v2rayN 界面手动添加具体的 `full:` 或 `domain:` 条目，不要使用 keyword。

---

*文档生成时间：2026-05-04 · 基于实际排错经验整理*
