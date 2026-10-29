"""
output.py - вывод симплекс-таблиц и итогового ответа на экран.
"""


def _fmt(val):
    # если число по сути целое - печать без точки
    if abs(val - round(val)) < 1e-9:
        return str(int(round(val)))
    return f"{val:.4g}"


def print_separator(title=""):
    line = "-" * 50
    if title:
        print(f"\n{line}")
        print(title)
        print(line)
    else:
        print(line)


def print_table(table, b_col, p_row, p_b_val, free_names, basis_names, iteration=None):
    """
    Печатает одну симплекс-таблицу: строки с базисными переменными
    и в конце строку p_j.
    """
    if iteration is not None:
        if iteration == 0:
            print("\nНачальная таблица:")
        else:
            print(f"\nИтерация {iteration}:")

    col_w = 8
    bas_w = 9
    all_cols = free_names + ["b"]
    n_cols = len(all_cols)

    top = "+" + "-" * bas_w + "+" + ("-" * col_w + "+") * n_cols
    mid = top

    print(top)
    header = "|" + "Базис".center(bas_w) + "|"
    for name in all_cols:
        header += name.center(col_w) + "|"
    print(header)
    print(mid)

    for i, name in enumerate(basis_names):
        row = "|" + name.center(bas_w) + "|"
        for j in range(len(free_names)):
            row += _fmt(table[i][j]).center(col_w) + "|"
        row += _fmt(b_col[i]).center(col_w) + "|"
        print(row)

    print(mid)

    p_str = "|" + "p_j".center(bas_w) + "|"
    for val in p_row:
        p_str += _fmt(val).center(col_w) + "|"
    p_str += _fmt(p_b_val).center(col_w) + "|"
    print(p_str)
    print(top)


def print_solution(result, n_original, goal):
    print_separator("Ответ")

    if not result.get("feasible"):
        print("Задача не имеет решений - область допустимых решений пуста.")
        return

    if not result.get("bounded"):
        print("Задача неограничена, целевая функция растёт бесконечно.")
        return

    x = result["x"]
    Z = result["Z"]

    print("Оптимальное решение:")
    for i in range(n_original):
        print(f"  x{i + 1} = {_fmt(x[i])}")

    print(f"\nZ_{goal} = {_fmt(Z)}")
