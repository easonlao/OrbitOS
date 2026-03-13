import re

files_to_fix = ['EN/AGENTS.md', 'EN/GEMINI.md']

translations = {
    '00_收件箱': '00_Inbox',
    '10_日记': '10_Daily',
    '20_项目': '20_Projects',
    '30_研究': '30_Research',
    '40_知识库': '40_Wiki',
    '50_资源': '50_Resources',
    '90_计划': '90_Plans',
    '99_系统': '99_System',
    '邮报/': 'Newsletters/',
    '产品发布/': 'ProductLaunches/',
    '模板, 提示词, 归档': 'Templates, Prompts, Archives',
    '模板, 提示词, 归档 (项目/YYYY/, 收件箱/YYYY/MM/)': 'Templates, Prompts, Archives (Projects/YYYY/, Inbox/YYYY/MM/)'
}

for file_path in files_to_fix:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for zh, en in translations.items():
        content = content.replace(zh, en)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
