with open('app/api/v1/auth.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from fastapi import APIRouter, Depends, HTTPException, status', 'from fastapi import APIRouter, Depends, HTTPException, status, Request\nfrom app.core.rate_limit import limiter')
content = content.replace('def register(\n    body: UserRegisterRequest,', 'def register(\n    request: Request,\n    body: UserRegisterRequest,')
content = content.replace('def login(\n    form_data', 'def login(\n    request: Request,\n    form_data')

# We need to insert @limiter.limit(...) after the router decorators.
# The route is: @router.post(\n    "/register",\n    ...
# We can just replace 'def register(' with '@limiter.limit("5/minute")\ndef register('
content = content.replace('def register(', '@limiter.limit("5/minute")\ndef register(')
content = content.replace('def login(', '@limiter.limit("10/minute")\ndef login(')

with open('app/api/v1/auth.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('app/api/v1/quests.py', 'r', encoding='utf-8') as f:
    content_quests = f.read()
content_quests = content_quests.replace('from fastapi import APIRouter, Depends, HTTPException, status', 'from fastapi import APIRouter, Depends, HTTPException, status, Request\nfrom app.core.rate_limit import limiter')
content_quests = content_quests.replace('def post_feedback(\n    attempt_id', 'def post_feedback(\n    request: Request,\n    attempt_id')
content_quests = content_quests.replace('def post_feedback(', '@limiter.limit("10/minute")\ndef post_feedback(')
with open('app/api/v1/quests.py', 'w', encoding='utf-8') as f:
    f.write(content_quests)

with open('app/api/v1/recommendations.py', 'r', encoding='utf-8') as f:
    content_recs = f.read()
content_recs = content_recs.replace('from fastapi import APIRouter, Depends, HTTPException, status', 'from fastapi import APIRouter, Depends, HTTPException, status, Request\nfrom app.core.rate_limit import limiter')
content_recs = content_recs.replace('def generate_recommendations(\n    db', 'def generate_recommendations(\n    request: Request,\n    db')
content_recs = content_recs.replace('def generate_recommendations(', '@limiter.limit("5/minute")\ndef generate_recommendations(')
with open('app/api/v1/recommendations.py', 'w', encoding='utf-8') as f:
    f.write(content_recs)
