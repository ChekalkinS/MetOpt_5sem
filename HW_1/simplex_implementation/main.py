"""
main.py - точка входа в программу.

Запуск:
  python main.py          - спросит задачу у пользователя
  python main.py --test   - решит задачу из нашего задания и покажет ответ
"""

import sys
from input import read_problem
from canonical import to_canonical
from simplex import solve
from output import print_solution, print_separator


def run_test():
    # наша задача: Z = 3x1 + x2 + 2x3 + 4x4 -> max
    # 2x1 + x2 + x3 <= 8
    # x1 + x3 + x4 = 6
    # x2 + x4 >= 4
    # ожидаемый ответ: x1=0, x2=8, x3=0, x4=6, Z=32
    from model import LPProblem

    print_separator("Тестовая задача из задания")
    print("Z = 3x1 + x2 + 2x3 + 4x4 -> max")
    print("2x1 + x2 + x3 <= 8")
    print("x1 + x3 + x4 = 6")
    print("x2 + x4 >= 4")

    problem = LPProblem(
        n_vars=4,
        c=[3.0, 1.0, 2.0, 4.0],
        goal="max",
        A=[
            [2.0, 1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
        ],
        b=[8.0, 6.0, 4.0],
        signs=["<=", "=", ">="],
    )

    canon = to_canonical(problem)

    print_separator("Канонический вид")
    print(f"Переменные: {canon.var_names}")
    print(f"c = {canon.c_ext}")

    result = solve(canon, output=True)
    print_solution(result, problem.n_vars, problem.goal)


def run_interactive():
    problem = read_problem()
    canon = to_canonical(problem)

    print_separator("Канонический вид")
    print(f"Переменные: {canon.var_names}")
    print(f"c = {canon.c_ext}")

    result = solve(canon, output=True)
    print_solution(result, problem.n_vars, problem.goal)


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test()
    else:
        run_interactive()
