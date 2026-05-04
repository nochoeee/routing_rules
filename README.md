# Clash → v2rayN 路由规则转换工具

> 将 Clash 配置文件转换为 v2rayN 兼容的路由规则  
> 完全兼容 v2rayN v7.x 和 Xray 26.x

---

## 🎯 项目简介

本工具可以将 Clash 的 `clash.yml` 配置文件转换为 v2rayN 可以直接导入的路由规则 JSON 文件。

转换过程严格遵循 Xray 26.x 的 LDH（Letter-Digit-Hyphen）语法规范,确保生成的规则文件可以正常导入和使用。

---

## ✨ 特性

- ✅ **完全自动化** - 一键转换,无需手动编辑
- ✅ **严格校验** - 自动过滤不符合 LDH 规范的域名
- ✅ **智能分组** - 按 Clash 策略自动分组
- ✅ **高保留率** - 98.4% 的规则成功转换
- ✅ **详细报告** - 提供完整的转换对比分析
- ✅ **中文文档** - 完整的中文使用说明

---

## 📦 转换结果

### 本次转换统计

| 项目 | 数值 |
|-----|------|
| 原始规则数 | 9,816 条 |
| 生成路由组 | 12 个 |
| 域名规则 | 9,146 条 |
| IP 规则 | 505 条 |
| 规则保留率 | 98.4% |

### 支持的规则类型

| Clash 规则 | 转换结果 | 状态 |
|-----------|---------|------|
| `DOMAIN` | `full:xxx` | ✅ 完全支持 |
| `DOMAIN-SUFFIX` | `domain:xxx` | ✅ 完全支持 |
| `IP-CIDR` | 独立数组元素 | ✅ 完全支持 |
| `IP-CIDR6` | 独立数组元素 | ✅ 完全支持 |
| `DST-PORT` | 逗号分隔 | ✅ 完全支持 |
| `DOMAIN-KEYWORD` | - | ❌ 已删除 |
| `GEOIP` | - | ❌ 已删除 |

---

## 🚀 快速开始

### 1. 运行转换脚本

```bash
python convert_clash_to_v2rayn.py
```

### 2. 导入到 v2rayN

1. 打开 v2rayN
2. 点击 `设置` → `路由设置`
3. **清空所有现有规则**（重要！）
4. 点击 `导入规则`
5. 选择 `v2rayn_routing_rules_new.json`
6. 点击 `确定`

### 3. 配置黑洞出站（可选）

如果使用了拦截广告功能:

1. 点击 `设置` → `参数设置`
2. 切换到 `Core:路由设置` 标签
3. 在出站设置中添加:
   - Tag: `block`
   - Protocol: `blackhole`

---

## 📚 文档说明

| 文件名 | 说明 | 推荐阅读 |
|-------|------|---------|
| [快速参考.md](./快速参考.md) | 一分钟快速导入指南 | ⭐⭐⭐ |
| [导入说明.md](./导入说明.md) | 详细的导入步骤和注意事项 | ⭐⭐⭐ |
| [转换对比报告.md](./转换对比报告.md) | 转换前后的详细对比分析 | ⭐⭐ |
| [Clash转v2rayN路由规则_解决方案.md](./Clash转v2rayN路由规则_解决方案.md) | 技术文档和踩坑记录 | ⭐ |

---

## ⚠️ 重要说明

### 已删除的规则类型

根据 Xray 26.x 的兼容性要求,以下规则已被删除:

#### 1. DOMAIN-KEYWORD 规则 (~100 条)

**删除原因**: Xray 26.x 对 keyword 类型执行严格的 LDH 校验

**影响的规则示例**:
```yaml
- DOMAIN-KEYWORD,steampipe,DIRECT
- DOMAIN-KEYWORD,steamcontent,DIRECT
- DOMAIN-KEYWORD,1drv,☁️ OneDrive
- DOMAIN-KEYWORD,onedrive,☁️ OneDrive
- DOMAIN-KEYWORD,google,🔰 选择节点
```

**补救方案**: 手动添加具体域名规则

#### 2. GEOIP 规则

**删除原因**: 可能引发兼容性问题

**补救方案**: 在 v2rayN 中手动配置地理位置路由

### 域名过滤规则

转换过程中自动过滤了以下不合法的域名:

- ❌ 不含 `.` 的单级域名
- ❌ Label 首尾有连字符的域名
- ❌ 含非 ASCII 字符的域名
- ❌ 空 label 或连续点的域名
- ❌ 占位符域名

---

## 🔧 技术细节

### LDH 规范

每个域名 label 必须满足:

```regex
^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?$
```

即:
- 只能包含字母、数字、连字符
- 不能以连字符开头或结尾
- 必须包含至少一个 `.`

### outboundTag 映射

| Clash 策略 | v2rayN outboundTag |
|-----------|-------------------|
| `DIRECT` | `direct` |
| `REJECT` | `block` |
| 其他代理策略 | `proxy` |

### IP 规则处理

- ✅ 每条 IP 作为独立数组元素
- ✅ 自动移除 `no-resolve` 参数
- ❌ 绝对不能用 `\n` 拼接

**正确格式**:
```json
{
  "ip": ["8.8.8.8/32", "1.1.1.1/32"]
}
```

**错误格式**:
```json
{
  "ip": ["8.8.8.8/32\n1.1.1.1/32"]  // ❌ 会导致解析失败
}
```

---

## 🛠️ 故障排除

### 问题 1: 导入后 v2rayN 报错

**解决方案**:
1. 完全清空旧规则
2. 重新导入 `v2rayn_routing_rules_new.json`
3. 如果仍然报错,尝试重装 v2rayN

### 问题 2: 某些网站无法访问

**可能原因**: 该网站的规则使用了已删除的 DOMAIN-KEYWORD

**解决方案**:
1. 查看 v2rayN 日志,找到被拦截的域名
2. 手动添加该域名的 `domain:` 规则

### 问题 3: 广告拦截不生效

**解决方案**: 按照上面的步骤配置 `block` 黑洞出站

---

## 📊 转换质量保证

### 验证通过的检查项

- ✅ 所有域名符合 LDH 规范
- ✅ IP 规则每条独立,无 `\n` 拼接
- ✅ 端口规则正确合并
- ✅ outboundTag 正确映射
- ✅ JSON 格式完全有效
- ✅ 无 DOMAIN-KEYWORD 残留
- ✅ 无 GEOIP 残留
- ✅ 无非法字符

### 兼容性确认

- ✅ v2rayN v7.x
- ✅ Xray-core 26.x
- ✅ Windows 10/11
- ✅ 支持 IPv4 和 IPv6

---

## 📝 更新日志

### v1.0 (2026-05-05)

- ✅ 首次发布
- ✅ 支持 Clash → v2rayN 转换
- ✅ 自动过滤非法域名
- ✅ 删除不兼容的 DOMAIN-KEYWORD 规则
- ✅ 完整的中文文档

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢以下项目:

- [Clash](https://github.com/Dreamacro/clash)
- [v2rayN](https://github.com/2dust/v2rayN)
- [Xray-core](https://github.com/XTLS/Xray-core)

---

## 📮 联系方式

如有问题或建议,请提交 Issue。

---

**最后更新**: 2026-05-05  
**版本**: v1.0  
**适用环境**: v2rayN v7.x · Xray 26.x · Windows
