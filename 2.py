import asyncio


async def do_something_async():
    await asyncio.sleep(2)
    return "Асинхронне завдання завершено"

start = asyncio.get_event_loop().time()
asyncio.run(do_something_async())
end = asyncio.get_event_loop().time()
print(f"Асинхронне виконання завершено за {end - start} секунд")