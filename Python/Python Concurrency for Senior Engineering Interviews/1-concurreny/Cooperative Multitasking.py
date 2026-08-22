import asyncio

async def task(name):
    for i in range(3):
        print(f"[{name}] Working step {i}")
        # EXPLICIT YIELD: We hand control back to the Event Loop here
        await asyncio.sleep(0.1)

async def main():
    # Schedule both tasks cooperatively on the single-threaded event loop
    async with asyncio.TaskGroup() as tg:
        tg.create_task(task("Task-1"))
        tg.create_task(task("Task-2"))

asyncio.run(main())