# Script kiểm tra translations
import re
import os

pattern = r'get_translation\(["\'](\w+)["\']\)'
all_keys_used = set()

# Scan UI folder
for root, dirs, files in os.walk('ui'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                keys = re.findall(pattern, content)
                all_keys_used.update(keys)

# Scan main files
for f in ['main.py', 'excel_importer.py']:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            keys = re.findall(pattern, file.read())
            all_keys_used.update(keys)

from translations import translations

missing = [k for k in sorted(all_keys_used) if k not in translations]
extra = [k for k in sorted(translations.keys()) if k not in all_keys_used]

print(f'Total keys used in code: {len(all_keys_used)}')
print(f'Total keys in translations.py: {len(translations)}')
print(f'Missing translations ({len(missing)}):')
for m in missing:
    print(f'  - {m}')
if missing:
    print()
print('Keys used in code:', sorted(all_keys_used)[-5:])
