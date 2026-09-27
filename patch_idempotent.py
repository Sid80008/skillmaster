import re

with open('app/services/recommendation_service.py', 'r', encoding='utf-8') as f:
    c = f.read()

replacement = '''    if existing is not None:
        # Idempotent return: if they already have an open recommendation, just return it
        return existing'''

c = re.sub(
    r'    if existing is not None:\n        raise ConflictError\([\s\S]*?\n        \)',
    replacement,
    c
)

with open('app/services/recommendation_service.py', 'w', encoding='utf-8') as f:
    f.write(c)
