# test_hh_api_direct.py
import asyncio
import aiohttp
import sys
import os

sys.path.append('src')


async def test_hh_api_direct():
    """Прямой тест API HH.ru"""
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": "Python",
        "area": 1,
        "per_page": 1
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                data = await response.json()

                if 'found' in data:
                    print(f"Found: {data['found']} vacancies")
                    print(f"Items: {len(data.get('items', []))}")
                else:
                    print("Error response:", data)

    except Exception as e:
        print(f"Error: {e}")


asyncio.run(test_hh_api_direct())
