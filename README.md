# nft_helper 帮助手册

## 目录

1. [简介](#1-简介)
2. [功能特性](#2-功能特性)
3. [系统要求](#3-系统要求)
4. [安装指南](#4-安装指南)
5. [快速开始](#5-快速开始)
6. [详细使用指南](#6-详细使用指南)
7. [命令参考](#7-命令参考)
8. [故障排除](#8-故障排除)
9. [常见问题](#9-常见问题)
10. [高级用法](#10-高级用法)

---

## 1. 简介

### 1.1 什么是 nft_helper？

nft_helper 是一个用于简化 nftables 防火墙规则管理的交互式辅助工具。它提供中文界面，让用户无需记忆复杂的 nft 命令语法即可轻松管理 Linux 防火墙规则。

### 1.2 什么是 nftables？

nftables 是 Linux 内核的新一代数据包过滤框架，取代了传统的 iptables。它提供更简洁的语法和更强大的功能。

### 1.3 为什么使用 nft_helper？

- **简单易用**：全中文交互界面
- **智能验证**：自动检查输入格式
- **安全执行**：所有命令执行前需要确认
- **自动安装**：自动检测并安装 nftables
- **多系统支持**：支持主流 Linux 发行版

---

## 2. 功能特性

### 2.1 核心功能

| 功能 | 说明 |
|------|------|
| 创建规则 | 支持单个端口、端口范围、多个端口 |
| 预设服务 | 快速配置 Web、SSH、邮件、数据库等服务 |
| IP 过滤 | 支持单个 IP、IP 范围、CIDR 网段 |
| 查询规则 | 清晰显示当前所有防火墙规则 |
| 删除规则 | 支持单条删除和批量删除 |
| 导出备份 | 将规则导出到文件 |
| 初始化 | 自动初始化防火墙表 |

### 2.2 完整协议模式预设服务

| 服务 | 协议 | 端口 |
|------|------|------|
| Web 服务 (HTTP/HTTPS) | TCP | 80, 443 |
| SSH 服务 | TCP | 22 |
| 邮件服务 | TCP | 25, 110, 143, 993, 995 |
| 数据库服务 | TCP | 3306 (MySQL), 5432 (PostgreSQL), 27017 (MongoDB) |
| 文件传输服务 | TCP | 21 (FTP) |
| DNS 服务 | TCP/UDP | 53 |

---

## 3. 系统要求

### 3.1 操作系统

| 支持的系统 | 包管理器 |
|------------|----------|
| Ubuntu | apt-get |
| Debian | apt-get |
| CentOS | yum / dnf |
| RHEL | yum / dnf |
| Fedora | dnf |
| Rocky Linux | dnf |
| AlmaLinux | dnf |
| Arch Linux | pacman |
| OpenSUSE | zypper |
| Alpine | apk |

### 3.2 依赖组件

- Python 3.6+
- nftables
- root 权限（安装和执行时）

### 3.3 Python 依赖

```
标准库：
- subprocess - 执行系统命令
- os - 系统操作
- json - 数据解析
- datetime - 时间处理
- tempfile - 临时文件
```

无需安装任何第三方库，纯 Python 实现。

---

## 4. 安装指南

### 4.1 快速安装

```bash
# 方法1：直接运行（推荐）
cd /path/to/nft_helper
chmod +x nft_helper.py
sudo ./nft_helper.py

# 方法2：安装到系统
./nft_helper.py
# 选择 8. 安装到系统

# 方法3：手动安装
sudo cp nft_helper.py /usr/local/bin/nft_helper
sudo chmod +x /usr/local/bin/nft_helper
nft_helper
```

### 4.2 卸载

```bash
# 运行程序后选择 9. 卸载
# 或手动删除
sudo rm /usr/local/bin/nft_helper
rm ~/.nft_helper_installed
```

### 4.3 权限说明

nftables 操作需要 root 权限，运行时会自动检测：

```
需要root权限来安装系统级工具。
请使用以下命令重新运行：
  sudo python3 /path/to/nft_helper.py
```

---

## 5. 快速开始

### 5.1 运行程序

```bash
sudo python3 nft_helper.py
```

### 5.2 主菜单介绍

```
==================================================
         nft命令执行辅助工具 v2.0
==================================================

欢迎使用nft命令执行辅助工具！
输入帮助信息查看详细使用指南。

==================================================
主菜单
==================================================
1. 创建新的nft规则
2. 完整协议模式（预设服务配置）
3. 查询当前防火墙规则
4. 导出规则到文件
5. 初始化防火墙表
6. 查看帮助信息
7. 安装指南
8. 安装到系统
9. 卸载
10. 退出

请输入选项编号:
```

### 5.3 创建第一条规则

**场景：阻止 TCP 5667 端口的入站连接**

```
请输入选项编号: 1

请选择操作类型：
1. 开放 (accept) - 允许流量通过
2. 拒绝 (drop)   - 丢弃流量
请输入选项编号: 2

请选择网络协议：
1. tcp    TCP - 传输控制协议（面向连接）
2. udp    UDP - 用户数据报协议（无连接）
...
请输入选项编号: 1

请输入端口号：
- 单个端口：如 22, 80, 443
- 端口范围：如 8080-8090
- 多个端口：用逗号分隔，如：80,443,8080
- 输入 'menu' 返回主菜单

请输入: 5667

请输入IP地址：
- 单个IP：如 192.168.1.100
- IP范围：如 192.168.1.0-192.168.1.255
- CIDR格式：如 192.168.1.0/24
- 直接回车：所有IP (0.0.0.0/0)
- 输入 'menu' 返回主菜单

请输入: 0.0.0.0/0

==================================================
准备执行的命令：
==================================================
1. nft add rule ip filter input ip daddr 0.0.0.0/0 tcp dport 5667 drop
==================================================

确认执行以上命令？(直接回车确认，输入 c 自定义命令):
```

按回车确认执行：

```
✓ 命令执行成功！
```

---

## 6. 详细使用指南

### 6.1 创建规则流程

#### 步骤 1：选择操作类型

| 选项 | 说明 |
|------|------|
| 开放 (accept) | 允许指定流量通过 |
| 拒绝 (drop) | 丢弃指定流量，不返回任何响应 |

#### 步骤 2：选择网络协议

| 选项 | 协议 | 适用场景 |
|------|------|----------|
| 1 | TCP | HTTP、HTTPS、SSH、FTP 等 |
| 2 | UDP | DNS、DHCP、游戏服务器等 |
| 3 | ICMP | ping、网络诊断等 |
| 4 | SCTP | 电信协议 |
| 5 | DCCP | 流媒体传输 |
| 6 | 其他 | 手动输入协议名 |
| 7 | 完整协议模式 | 使用预设服务配置 |
| 8 | 返回主菜单 | 取消操作 |

#### 步骤 3：输入端口号

**格式说明**：

```
单个端口：      22        → TCP 22
端口范围：      8080-8090 → TCP 8080-8090
多个端口：      80,443   → TCP 80 和 TCP 443
```

**示例**：

```
请输入: 80               # 单个端口
请输入: 8080-8090       # 端口范围
请输入: 80,443,8080     # 多个端口
```

#### 步骤 4：输入 IP 地址（可选）

```
单个IP：       192.168.1.100              # 仅匹配该IP
IP范围：       192.168.1.0-192.168.1.255  # 范围内的所有IP
CIDR格式：     192.168.1.0/24              # 子网掩码格式
直接回车：     (空)                         # 所有IP (0.0.0.0/0)
```

**示例**：

```
请输入: 192.168.1.100         # 阻止来自 192.168.1.100 的连接
请输入: 10.0.0.0/8           # 阻止来自 10.x.x.x 网段的连接
请输入: (直接回车)           # 阻止所有IP的连接
```

### 6.2 完整协议模式

快速配置常用服务的预设方案：

```
请输入选项编号: 2

完整协议模式 - 选择您要配置的服务：
1. Web服务 (HTTP/HTTPS)
2. SSH服务 (TCP 22)
3. 邮件服务 (SMTP/POP3/IMAP)
4. 数据库服务 (MySQL/PostgreSQL/MongoDB)
5. 文件传输服务 (FTP/SFTP)
6. DNS服务 (TCP/UDP 53)
7. 返回主菜单
```

选择后同样需要选择操作类型（开放/拒绝）。

### 6.3 查询当前规则

```
请输入选项编号: 3

============================================================
当前防火墙规则 - INPUT链
============================================================

端口规则列表：
----------------------------------------
[ 1] 端口 5667 ip daddr 0.0.0.0/0 拒绝
[ 2] 端口 80 ip daddr 0.0.0.0/0 放行
----------------------------------------
共 2 条端口规则

============================================================
操作选项
============================================================
1. 删除规则
2. 查看JSON格式
3. 返回主菜单

选择操作:
```

### 6.4 删除规则

在查询规则界面选择"1. 删除规则"：

```
输入要删除的规则编号，多个用逗号分隔（1-2），或输入 'menu' 返回主菜单
格式: 编号或 1,3,4

输入: 1

将删除以下规则：
  1. nft delete rule ip filter input handle 10

确认执行以上命令？(直接回车确认):
```

**批量删除示例**：

```
输入: 1,2           # 同时删除编号1和2的规则
输入: 1-3           # 无效，暂不支持范围
```

### 6.5 导出规则

```
请输入选项编号: 4

============================================================
导出防火墙规则
============================================================

正在导出当前防火墙规则...

✓ 规则已导出到文件：nft_rules_backup_20240115_120000.txt

导出的内容包括：
- 所有防火墙表的配置
- INPUT、OUTPUT、FORWARD 链的规则
- 完整的 nftables 规则集

============================================================
```

---

## 7. 命令参考

### 7.1 常用 nft 命令

| 功能 | nft 命令 |
|------|----------|
| 列出所有规则 | `nft list ruleset` |
| 列出规则（含handle） | `nft list ruleset -a` |
| JSON格式输出 | `nft -j list ruleset` |
| 添加规则 | `nft add rule ip filter input tcp dport 80 accept` |
| 插入规则 | `nft insert rule ip filter input tcp dport 80 accept` |
| 删除规则 | `nft delete rule ip filter input handle 10` |
| 清空规则 | `nft flush ruleset` |
| 查看表 | `nft list tables` |
| 删除表 | `nft delete table ip filter` |

### 7.2 常见场景示例

**开放 HTTP 服务（80端口）**

```bash
nft add rule ip filter input tcp dport 80 accept
```

**开放 HTTPS 服务（443端口）**

```bash
nft add rule ip filter input tcp dport 443 accept
```

**开放 SSH（仅特定IP）**

```bash
nft add rule ip filter input ip daddr 192.168.1.100 tcp dport 22 accept
```

**阻止所有来自特定网段的连接**

```bash
nft add rule ip filter input ip daddr 10.0.0.0/8 drop
```

**开放端口范围**

```bash
nft add rule ip filter input tcp dport 8080-8090 accept
```

**查看当前规则**

```bash
nft -j list ruleset | jq .
```

---

## 8. 故障排除

### 8.1 常见错误

#### 错误 1：权限不足

```
✗ 权限不足，无法写入安装目录。
```

**解决方法**：
```bash
sudo python3 nft_helper.py
```

#### 错误 2：nftables 未安装

```
✗ 未找到 nftables 工具。
```

**自动解决**：程序会提示自动安装

**手动解决**：
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install nftables

# CentOS/RHEL
sudo yum install nftables
# 或
sudo dnf install nftables

# Arch
sudo pacman -S nftables
```

#### 错误 3：表不存在

```
✗ Could not process rule: No such file or directory
```

**解决方法**：
```bash
# 初始化表
sudo nft add table ip filter
sudo nft add chain ip filter input { type filter hook input priority 0 \; policy accept \; }
```

**自动解决**：程序会自动检测并初始化

#### 错误 4：端口号无效

```
✗ 端口号必须在1-65535之间。
```

**原因**：输入了超出范围的端口号

**解决方法**：检查端口号，确保在 1-65535 范围内

#### 错误 5：IP地址格式无效

```
✗ IP地址格式无效：...
```

**原因**：输入了格式错误的 IP 地址

**解决方法**：
- 单个 IP：`192.168.1.100`
- CIDR 网段：`192.168.1.0/24`
- IP 范围：`192.168.1.0-192.168.1.255`

### 8.2 日志文件

程序运行日志保存在当前目录：

```
nft_helper.log
```

日志内容包括：
- 操作时间
- 操作类型
- 执行结果
- 错误信息

查看日志：
```bash
tail -f nft_helper.log
```

---

## 9. 常见问题

### Q1：规则是立即生效的吗？

**答**：是的，nftables 规则立即生效，无需重启服务。

### Q2：重启后规则会丢失吗？

**答**：默认情况下 nftables 规则不会自动持久化。需要配置服务使其开机启动：

```bash
# Ubuntu/Debian
sudo systemctl enable nftables
sudo systemctl start nftables

# 保存当前规则
nft list ruleset > /etc/nftables.conf
```

### Q3：如何备份和恢复规则？

**答**：使用程序导出功能或在命令行：

```bash
# 备份
nft -j list ruleset > backup.json

# 恢复
nft -f backup.json
```

### Q4：INPUT 链和 OUTPUT 链有什么区别？

| 链 | 方向 | 说明 |
|----|------|------|
| INPUT | 入站 | 进入服务器的流量 |
| OUTPUT | 出站 | 从服务器出去的流量 |
| FORWARD | 转发 | 经过服务器转发的流量 |

### Q5：accept 和 drop 有什么区别？

| 动作 | 效果 | 日志 |
|------|------|------|
| accept | 允许流量通过 | 无记录 |
| drop | 丢弃流量，不响应 | 无记录 |
| reject | 拒绝流量，返回错误 | 可选记录 |

### Q6：如何限制特定国家/地区的 IP？

**答**：程序暂不支持此功能。可使用第三方工具如：

```bash
# 使用 geoip 数据库
# 安装 xtables-addons
sudo apt-get install xtables-addons-dkms
```

### Q7：规则顺序重要吗？

**答**：非常重要。nftables 按顺序匹配规则，匹配到第一条后停止。

**建议**：
- 通用规则放后面
- 具体规则放前面
- 阻止规则放最后

### Q8：如何测试规则是否生效？

```bash
# 从外部测试端口连通性
telnet <服务器IP> <端口>
nc -zv <服务器IP> <端口>

# 本地测试
nc -lvp <端口>

# 查看连接状态
ss -tlnp
netstat -tlnp
```

### Q9：程序支持 IPv6 吗？

**答**：当前版本主要支持 IPv4。IPv6 规则需要手动添加：

```bash
nft add rule ip6 filter input tcp dport 80 accept
```

### Q10：如何完全禁用防火墙？

**答**：不推荐，但可以：

```bash
# 清空所有规则
nft flush ruleset

# 或停止服务
sudo systemctl stop nftables
sudo systemctl disable nftables
```

---

## 10. 高级用法

### 10.1 自定义命令

在确认执行时输入 `c` 可以自定义命令：

```
确认执行以上命令？(直接回车确认，输入 c 自定义命令): c
请输入自定义命令: nft add rule ip filter input tcp dport 22 ip saddr 192.168.1.0/24 accept
```

### 10.2 脚本化使用

```bash
#!/bin/bash
# 创建规则脚本示例

# 开放SSH
echo "y" | python3 nft_helper.py <<EOF
1
1
1
22

EOF
```

### 10.3 批量操作

通过命令行直接使用 nft：

```bash
# 批量添加规则
nft -f - <<EOF
table ip filter {
    chain input {
        tcp dport 80 accept
        tcp dport 443 accept
        ip daddr 192.168.1.0/24 tcp dport 22 accept
        ct state established,related accept
        drop
    }
}
EOF
```

### 10.4 性能优化建议

| 建议 | 说明 |
|------|------|
| 减少规则数量 | 过多的规则会影响性能 |
| 使用集合 | 用 `{}` 分组多个端口 |
| 使用链 | 按服务类型组织规则 |
| 合理排序 | 常用规则放前面 |

### 10.5 安全最佳实践

1. **默认拒绝策略**
   ```
   nft add rule ip filter input drop
   ```

2. **仅开放必要端口**
   ```
   # 只开放80、443
   nft add rule ip filter input tcp dport {80, 443} accept
   ```

3. **限制管理IP**
   ```
   # 只允许192.168.1.100管理
   nft add rule ip filter input ip saddr 192.168.1.100 tcp dport 22 accept
   ```

4. **记录被拒绝的连接**
   ```
   nft add rule ip filter input drop log
   ```

5. **定期审查规则**
   ```
   nft list ruleset
   ```

---

## 附录

### A. 相关资源

- [nftables 官方文档](https://wiki.nftables.org/)
- [Arch Wiki - nftables](https://wiki.archlinux.org/title/nftables)
- [Debian nftables](https://wiki.debian.org/nftables)

### B. 错误代码

| 代码 | 说明 |
|------|------|
| E001 | 权限不足 |
| E002 | nftables 未安装 |
| E003 | 无效的端口号 |
| E004 | 无效的 IP 地址 |
| E005 | 表或链不存在 |
| E006 | 规则不存在 |

### C. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v2.0 | 2026-02-08 | 新增自动安装、多选删除、IP过滤、系统检测 |
| v1.0 | 2023-06 | 初始版本 |

---

## 反馈

如有问题或建议，请：
1. 查看日志文件：`nft_helper.log`
2. 运行测试：`python3 nft_helper.py --test`
3. 提交 Issue 或联系开发者

---

**文档版本**: v2.0  
**最后更新**: 2026-02-08  
**适用版本**: nft_helper v2.0+
