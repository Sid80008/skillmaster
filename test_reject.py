import asyncio
import httpx

async def test_flow():
    async with httpx.AsyncClient(base_url="https://skillmaster-bfx7.onrender.com") as client:
        # 1. Login
        resp = await client.post("/api/v1/auth/token", data={"username": "testuser_999", "password": "password123"})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Generate
        resp = await client.post("/api/v1/recommendations/", headers=headers)
        if resp.status_code not in (200, 201):
            print("Generate failed:", resp.text)
            return
        rec_id = resp.json()["id"]
        
        # 3. Present
        resp = await client.post(f"/api/v1/recommendations/{rec_id}/present", headers=headers)
        print("Present:", resp.status_code)
        
        # 4. Reject
        resp = await client.post(f"/api/v1/recommendations/{rec_id}/reject", headers=headers, json={"reason": None})
        print("Reject:", resp.status_code, resp.text)

asyncio.run(test_flow())
