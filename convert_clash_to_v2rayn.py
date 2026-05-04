#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clash 路由规则转换为 v2rayN 格式
根据解决方案文档中的规则进行转换
"""

import yaml
import json
import re
from typing import List, Dict, Set

def is_valid_domain_entry(entry: str) -> bool:
    """
    验证域名条目是否符合 LDH 规范
    """
    # 提取前缀
    if entry.startswith('full:'):
        val = entry[5:]
    elif entry.startswith('domain:'):
        val = entry[7:]
    else:
        return False
    
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
        # LDH 规范：只含字母/数字/连字符，且不以连字符开头或结尾
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?$', label):
            return False
    
    return True

def convert_outbound_tag(clash_policy: str) -> str:
    """
    转换 Clash 策略到 v2rayN outboundTag
    """
    if clash_policy == 'DIRECT':
        return 'direct'
    elif clash_policy == 'REJECT':
        return 'block'
    else:
        return 'proxy'

def process_clash_rules(rules: List[str]) -> Dict[str, Dict]:
    """
    处理 Clash 规则并按策略分组
    """
    # 按策略分组存储规则
    grouped_rules = {}
    
    for rule in rules:
        parts = rule.split(',')
        if len(parts) < 2:
            continue
        
        rule_type = parts[0].strip()
        rule_value = parts[1].strip()
        policy = parts[2].strip() if len(parts) > 2 else 'DIRECT'
        
        # 跳过 MATCH 规则
        if rule_type == 'MATCH':
            continue
        
        # 跳过所有 DOMAIN-KEYWORD 规则（根据解决方案）
        if rule_type == 'DOMAIN-KEYWORD':
            continue
        
        # 跳过 GEOIP 规则
        if rule_type == 'GEOIP':
            continue
        
        # 初始化策略组
        if policy not in grouped_rules:
            grouped_rules[policy] = {
                'domains': [],
                'ips': [],
                'ports': []
            }
        
        # 处理不同类型的规则
        if rule_type == 'DOMAIN':
            domain_entry = f'full:{rule_value}'
            if is_valid_domain_entry(domain_entry):
                grouped_rules[policy]['domains'].append(domain_entry)
        
        elif rule_type == 'DOMAIN-SUFFIX':
            domain_entry = f'domain:{rule_value}'
            if is_valid_domain_entry(domain_entry):
                grouped_rules[policy]['domains'].append(domain_entry)
        
        elif rule_type in ['IP-CIDR', 'IP-CIDR6']:
            # 移除 no-resolve 参数
            ip_value = rule_value.split(',')[0] if ',' in rule_value else rule_value
            grouped_rules[policy]['ips'].append(ip_value)
        
        elif rule_type == 'DST-PORT':
            grouped_rules[policy]['ports'].append(rule_value)
    
    return grouped_rules

def create_v2rayn_rules(grouped_rules: Dict[str, Dict]) -> List[Dict]:
    """
    创建 v2rayN 路由规则
    """
    v2rayn_rules = []
    
    for policy, rules in grouped_rules.items():
        outbound_tag = convert_outbound_tag(policy)
        
        # 合并端口（用逗号分隔）
        port_str = ','.join(rules['ports']) if rules['ports'] else ''
        
        # 创建规则对象
        rule_obj = {
            'port': port_str,
            'outboundTag': outbound_tag,
            'domain': rules['domains'],
            'ip': rules['ips'],
            'enabled': True,
            'remarks': policy
        }
        
        v2rayn_rules.append(rule_obj)
    
    return v2rayn_rules

def main():
    print('开始转换 Clash 配置到 v2rayN 格式...')
    
    # 读取 Clash 配置
    print('读取 clash.yml...')
    with open('clash.yml', 'r', encoding='utf-8') as f:
        clash_config = yaml.safe_load(f)
    
    # 提取规则
    rules = clash_config.get('rules', [])
    print(f'找到 {len(rules)} 条规则')
    
    # 处理规则
    print('处理规则...')
    grouped_rules = process_clash_rules(rules)
    print(f'分组为 {len(grouped_rules)} 个策略组')
    
    # 创建 v2rayN 规则
    print('生成 v2rayN 规则...')
    v2rayn_rules = create_v2rayn_rules(grouped_rules)
    
    # 统计信息
    total_domains = sum(len(r['domain']) for r in v2rayn_rules)
    total_ips = sum(len(r['ip']) for r in v2rayn_rules)
    print(f'生成 {len(v2rayn_rules)} 条路由规则')
    print(f'  - 域名规则: {total_domains} 条')
    print(f'  - IP 规则: {total_ips} 条')
    
    # 保存为 JSON
    output_file = 'v2rayn_routing_rules_new.json'
    print(f'保存到 {output_file}...')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(v2rayn_rules, f, ensure_ascii=False, indent=2)
    
    print('转换完成!')
    print(f'\n请在 v2rayN 中导入 {output_file}')
    print('\n注意事项:')
    print('1. 导入前请先清空 v2rayN 中的现有路由规则')
    print('2. 如果使用了 REJECT 策略,需要手动添加一个 tag 为 "block" 的黑洞出站')
    print('3. 所有 DOMAIN-KEYWORD 规则已被删除(Xray 26.x 不支持)')
    print('4. 所有 GEOIP 规则已被删除')

if __name__ == '__main__':
    main()
