"""
canonical.py - приведение задачи к каноническому виду

Шаги:
1. Если задача на максимум, замена знака у всей целевой функции, чтобы
   получить минимум.
2. Для ограничений со знаком <= добавление доп. переменной с коэффициентом +1.
   Для ограничений со знаком >= добавление доп. переменной с коэффициентом -1.
   Если ограничение уже равенство, ничего не добавляется.
3. Если после этого b меньше нуля, умножение всего ограничения на -1.
4. Пытаемся сразу найти базис - вдруг он уже есть без искусственных переменных.
"""

from model import LPProblem, CanonicalProblem


def to_canonical(prob: LPProblem) -> CanonicalProblem:
    m = len(prob.b)
    n = prob.n_vars

    # шаг 1: если задача на максимум, смена знака коэффициентов c
    if prob.goal == "max":
        c = [-ci for ci in prob.c]
    else:
        c = list(prob.c)

    A = [list(row) for row in prob.A]
    b = list(prob.b)
    signs = list(prob.signs)

    # шаг 2: подсчет сколько доп. переменных нужно, расширение матрицы
    n_extra = sum(1 for s in signs if s != "=")
    n_total = n + n_extra

    for row in A:
        row += [0.0] * n_extra
    c += [0.0] * n_extra

    var_names = [f"x{j + 1}" for j in range(n_total)]

    extra_col = n
    for i in range(m):
        if signs[i] == "<=":
            A[i][extra_col] = 1.0
            extra_col += 1
        elif signs[i] == ">=":
            A[i][extra_col] = -1.0
            extra_col += 1

    # шаг 3: если b отрицательное, замена знака всей строки
    for i in range(m):
        if b[i] < 0:
            A[i] = [-aij for aij in A[i]]
            b[i] = -b[i]

    # шаг 4: базис без искусственных переменных
    basis = _find_basis(A, m, n_total)

    return CanonicalProblem(
        c_ext=c,
        A_ext=A,
        b=b,
        n_original=n,
        n_total=n_total,
        var_names=var_names,
        basis=basis,
        goal=prob.goal,
    )


def _find_basis(A, m, n_total):
    """
    Ищем для каждой строки столбец с единицей, который во всех остальных
    строках равен нулю. Если для строки такого столбца нет, ставим -1 -
    это значит, что для неё понадобится искусственная переменная.
    """
    basis = [-1] * m

    for i in range(m):
        for j in range(n_total):
            if abs(A[i][j] - 1.0) < 1e-9:
                is_unit_column = True
                for k in range(m):
                    if k != i and abs(A[k][j]) > 1e-9:
                        is_unit_column = False
                        break
                if is_unit_column and j not in basis:
                    basis[i] = j
                    break

    return basis
