import re

files_to_fix = ['EN/AGENTS.md', 'EN/GEMINI.md']

translations = {
    '项目/YYYY/, 收件箱/YYYY/MM/': 'Projects/YYYY/, Inbox/YYYY/MM/'
}

for file_path in files_to_fix:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for zh, en in translations.items():
        content = content.replace(zh, en)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
