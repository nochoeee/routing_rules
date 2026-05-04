# v2rayN v7.21 配置黑洞出站指南

> 针对 v2rayN v7.21 版本的详细配置说明

---

## 🎯 问题说明

在 v2rayN v7.21 版本中,界面布局与之前版本不同,无法通过图形界面直接添加黑洞出站。需要通过编辑配置文件来实现。

---

## 🔧 三种解决方案

### 方案 1: 编辑 Xray 配置文件 (推荐)

**适用场景**: 需要真正的广告拦截功能

**步骤**:

1. **打开配置文件**
   - 在 v2rayN 主界面,点击菜单栏 `设置` → `参数设置`
   - 切换到 `Core: 基础设置` 标签
   - 点击 `编辑配置文件` 按钮

2. **找到 outbounds 部分**
   
   配置文件中会有类似这样的结构:
   ```json
   {
     "outbounds": [
       {
         "tag": "proxy",
         "protocol": "vmess",
         ...
       },
       {
         "tag": "direct",
         "protocol": "freedom",
         ...
       }
     ]
   }
   ```

3. **添加黑洞出站**
   
   在 `outbounds` 数组的末尾添加:
   ```json
   {
     "tag": "block",
     "protocol": "blackhole",
     "settings": {
       "response": {
         "type": "http"
       }
     }
   }
   ```

4. **完整示例**:
   ```json
   {
     "outbounds": [
       {
         "tag": "proxy",
         "protocol": "vmess",
         "settings": { ... }
       },
       {
         "tag": "direct",
         "protocol": "freedom",
         "settings": {}
       },
       {
         "tag": "block",
         "protocol": "blackhole",
         "settings": {
           "response": {
             "type": "http"
           }
         }
       }
     ]
   }
   ```

5. **保存并重启**
   - 保存配置文件
   - 重启 v2rayN 或重新加载配置

---

### 方案 2: 修改路由规则文件 (最简单)

**适用场景**: 不需要广告拦截,或者觉得配置太复杂

**步骤**:

1. **用文本编辑器打开** `v2rayn_routing_rules_new.json`

2. **查找并替换**
   - 查找: `"outboundTag": "block"`
   - 替换为: `"outboundTag": "direct"`

3. **或者删除拦截规则**
   
   找到并删除这个规则对象:
   ```json
   {
     "port": "",
     "outboundTag": "block",
     "domain": [],
     "ip": [],
     "enabled": true,
     "remarks": "🛑 拦截广告"
   }
   ```

4. **保存文件**,然后导入到 v2rayN

**优点**:
- ✅ 最简单,不需要编辑复杂的配置文件
- ✅ 不会因为缺少 block 出站而报错

**缺点**:
- ❌ 失去广告拦截功能(广告会直连而不是被拦截)

---

### 方案 3: 使用 v2rayN 的自定义配置

**适用场景**: 熟悉 Xray 配置的高级用户

**步骤**:

1. **创建自定义配置文件**
   - 在 v2rayN 安装目录下创建 `custom_outbounds.json`

2. **添加黑洞出站配置**:
   ```json
   [
     {
       "tag": "block",
       "protocol": "blackhole",
       "settings": {
         "response": {
           "type": "http"
         }
       }
     }
   ]
   ```

3. **在 v2rayN 中引用**
   - 打开 `设置` → `参数设置` → `Core: 基础设置`
   - 在 `自定义配置` 中引用此文件

---

## 🔍 验证配置是否生效

### 方法 1: 查看日志

1. 在 v2rayN 主界面,点击菜单栏 `帮助` → `查看日志`
2. 查找是否有 `block` 相关的错误信息
3. 如果没有错误,说明配置成功

### 方法 2: 测试广告拦截

1. 访问一个有广告的网站
2. 如果广告被拦截(无法加载),说明配置成功
3. 如果广告仍然显示,检查配置是否正确

---

## 📋 完整配置示例

### Xray 配置文件示例 (config.json)

```json
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 10808,
      "protocol": "socks",
      "settings": {
        "udp": true
      }
    }
  ],
  "outbounds": [
    {
      "tag": "proxy",
      "protocol": "vmess",
      "settings": {
        "vnext": [
          {
            "address": "your-server.com",
            "port": 443,
            "users": [
              {
                "id": "your-uuid",
                "alterId": 0
              }
            ]
          }
        ]
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {}
    },
    {
      "tag": "block",
      "protocol": "blackhole",
      "settings": {
        "response": {
          "type": "http"
        }
      }
    }
  ],
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "outboundTag": "block",
        "domain": [
          "geosite:category-ads-all"
        ]
      },
      {
        "type": "field",
        "outboundTag": "direct",
        "domain": [
          "geosite:cn"
        ]
      },
      {
        "type": "field",
        "outboundTag": "direct",
        "ip": [
          "geoip:cn",
          "geoip:private"
        ]
      }
    ]
  }
}
```

---

## ⚠️ 常见问题

### Q1: 编辑配置文件后 v2rayN 无法启动?

**A**: 配置文件格式错误

**解决方案**:
1. 检查 JSON 格式是否正确(逗号、括号是否匹配)
2. 使用 JSON 验证工具检查: https://jsonlint.com/
3. 恢复备份的配置文件

### Q2: 添加 block 出站后仍然看到广告?

**A**: 路由规则未生效

**解决方案**:
1. 检查路由规则中的 `outboundTag` 是否为 `block`
2. 检查路由规则是否已启用 (`enabled: true`)
3. 重启 v2rayN

### Q3: 不想配置黑洞出站,有其他方法吗?

**A**: 使用方案 2,将 `block` 改为 `direct`

**优点**: 简单,不会报错  
**缺点**: 失去广告拦截功能

---

## 🎯 推荐方案

### 如果你想要广告拦截功能
→ 使用 **方案 1**: 编辑 Xray 配置文件

### 如果你觉得配置太复杂
→ 使用 **方案 2**: 修改路由规则文件,将 block 改为 direct

### 如果你是高级用户
→ 使用 **方案 3**: 自定义配置文件

---

## 📝 配置文件位置

| 文件 | 位置 |
|-----|------|
| v2rayN 配置 | `v2rayN安装目录/guiNConfig.json` |
| Xray 配置 | `v2rayN安装目录/config.json` |
| 路由规则 | 导入时选择的 `v2rayn_routing_rules_new.json` |

---

## 🔄 配置后的操作

1. **保存配置文件**
2. **重启 v2rayN** 或点击 `重新加载配置`
3. **测试连接** 确保代理正常工作
4. **测试广告拦截** 访问有广告的网站

---

## 📚 相关文档

- [快速参考.md](./快速参考.md) - 快速导入指南
- [导入说明.md](./导入说明.md) - 详细导入步骤
- [Xray 配置文档](https://xtls.github.io/config/) - 官方配置文档

---

**文档版本**: v1.0  
**适用版本**: v2rayN v7.21  
**最后更新**: 2026-05-05
