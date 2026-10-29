"""
input.py - ввод задачи линейного программирования от пользователя.
"""

from model import LPProblem


def _read_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Ошибка: нужно ввести число.")


def _read_int(prompt, min_val=1):
    while True:
        try:
            val = int(input(prompt))
            if val < min_val:
                print(f"Ошибка: значение должно быть не меньше {min_val}.")
            else:
                return val
        except ValueError:
            print("Ошибка: нужно ввести целое число.")


def _read_sign(prompt):
    valid = {"<=", "=", ">="}
    while True:
        val = input(prompt).strip()
        if val in valid:
            return val
        print("Ошибка: знак должен быть одним из: <=, =, >=")


def _read_goal(prompt):
    while True:
        val = input(prompt).strip().lower()
        if val in ("min", "max"):
            return val
        print("Ошибка: введите min или max.")


def read_problem():
    """
    Спрашивает у пользователя задачу по шагам и возвращает объект LPProblem.
    """
    print("=" * 50)
    print("Ввод задачи линейного программирования")
    print("=" * 50)

    n = _read_int("Количество переменных: ")
    m = _read_int("Количество ограничений: ")

    print(f"\nКоэффициенты целевой функции (c1...c{n}):")
    c = []
    for j in range(1, n + 1):
        c.append(_read_float(f"  c{j} = "))

    goal = _read_goal("Тип задачи (min или max): ")

    print("\nТеперь вводим ограничения по одному.")
    A = []
    b = []
    signs = []

    for i in range(1, m + 1):
        print(f"\nОграничение {i}:")
        row = []
        for j in range(1, n + 1):
            row.append(_read_float(f"  a{i}{j} = "))
        A.append(row)
        signs.append(_read_sign("  Знак (<=, = или >=): "))
        b.append(_read_float(f"  b{i} = "))

    return LPProblem(n_vars=n, c=c, goal=goal, A=A, b=b, signs=signs)
