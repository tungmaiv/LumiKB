"""Quick test to debug cookie issue."""
import asyncio
import pytest

# Run from backend directory

async def test_debug():
    from tests.factories import create_registration_data
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app, raise_app_exceptions=False)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        user_data = create_registration_data()
        reg_resp = await client.post("/api/v1/auth/register", json=user_data)
        print(f"Register: {reg_resp.status_code}")

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        print(f"Login: {login_resp.status_code}")
        print(f"Login cookies: {login_resp.cookies}")
        print(f"Login cookies dict: {dict(login_resp.cookies)}")

        # Try chat with cookies
        chat_resp = await client.post(
            "/api/v1/chat",
            cookies=login_resp.cookies,
            json={"kb_id": "test", "message": "test"}
        )
        print(f"Chat: {chat_resp.status_code}")
        print(f"Chat response: {chat_resp.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_debug())
