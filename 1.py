import time


def do_something():
    time.sleep(2)
    return "Завдання завершено"

start = time.time()
do_something()
end = time.time()
print(f"Виконано за {end - start} секунд")