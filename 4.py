import asyncio

async def simple_delay():
    print("Початок задачі")
    await asyncio.sleep(2)
    print("Завершення задачі")

asyncio.run(simple_delay())