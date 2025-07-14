import asyncio


async def factorial(n):
    if n == 0:
        return 1
    else:
        return n * await factorial(n-1)

async def main():
    result = await factorial(10)
    print(f"Факторіал 10 = {result}")

asyncio.run(main())

def factorial1(n):
    if n == 0:
        return 1
    else:
        return n * factorial1(n-1)

result = factorial1(10)
print(f"Факторіал 10 = {result}")