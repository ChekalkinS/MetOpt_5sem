"""
simplex.py - сам алгоритм симплекс-метода, реализован по шагам из методички.

Как решаем задачу:
1. Смотрим, нашёлся ли базис сразу после канонического вида.
2. Если нет, строим вспомогательную задачу с искусственными переменными
   и решаем её, чтобы найти начальный базис.
3. Решаем основную задачу итерациями симплекс-метода.

Формулы пересчёта таблицы на каждой итерации (разрешающий элемент a[i*][j*]):
  новое a[i*][j*] = 1 / a[i*][j*]
  новое a[i*][j]  = a[i*][j] / a[i*][j*]       - разрешающая строка
  новое a[i][j*]  = -a[i][j*] / a[i*][j*]      - разрешающий столбец
  новое a[i][j]   = a[i][j] - a[i*][j]*a[i][j*]/a[i*][j*]   - все остальные
То же самое применяется и к столбцу b, и к строке p_j - они пересчитываются
по тем же формулам, просто их удобно хранить отдельно от основной таблицы.
"""

from model import CanonicalProblem
from output import print_table, print_separator


def _pivot_with_b(table, b_col, p_row, p_b_val, row, col):
    """
    Делает один шаг симплекс-метода: пересчитывает таблицу, столбец b
    и строку p_j вокруг разрешающего элемента table[row][col].
    """
    m = len(table)
    n = len(table[0])
    pivot = table[row][col]

    new_table = [[0.0] * n for _ in range(m)]
    new_b = list(b_col)
    new_p = list(p_row)

    # разрешающая строка делится на разрешающий элемент
    for j in range(n):
        if j == col:
            new_table[row][j] = 1.0 / pivot
        else:
            new_table[row][j] = table[row][j] / pivot
    new_b[row] = b_col[row] / pivot

    # разрешающий столбец для остальных строк
    for i in range(m):
        if i != row:
            new_table[i][col] = -table[i][col] / pivot
    new_p[col] = -p_row[col] / pivot

    # все остальные элементы таблицы
    for i in range(m):
        if i != row:
            for j in range(n):
                if j != col:
                    new_table[i][j] = table[i][j] - table[row][j] * table[i][col] / pivot
            new_b[i] = b_col[i] - b_col[row] * table[i][col] / pivot

    # остальные элементы строки p_j
    for j in range(n):
        if j != col:
            new_p[j] = p_row[j] - table[row][j] * p_row[col] / pivot

    new_p_b = p_b_val - b_col[row] * p_row[col] / pivot

    return new_table, new_b, new_p, new_p_b


MAX_ITERATIONS = 1000


def _choose_pivot_col(p_row, free_cols=None, bland=False):
    """
    Выбор разрешающего столбца.

    Обычный режим (по методичке): берём минимальный отрицательный p_j.
    Режим Бленда (bland=True): среди всех отрицательных p_j берём тот,
    у которого наименьший номер переменной. Это защита от зацикливания
    на вырожденных вершинах - включается только когда предыдущий шаг
    был вырожденным (b разрешающей строки был равен 0).
    Если отрицательных p_j нет - решение оптимально, возвращаем -1.
    """
    col = -1
    if bland and free_cols is not None:
        best_var = None
        for j, val in enumerate(p_row):
            if val < -1e-9 and (best_var is None or free_cols[j] < best_var):
                best_var = free_cols[j]
                col = j
        return col

    min_val = 0.0
    for j, val in enumerate(p_row):
        if val < min_val - 1e-9:
            min_val = val
            col = j
    return col


def _choose_pivot_row(table, b_col, col, basis=None):
    """
    Выбор разрешающей строки: среди строк с положительным коэффициентом
    в разрешающем столбце берём ту, где b_i / a_ij минимально.
    При равных отношениях берём строку с наименьшим номером базисной
    переменной (вторая половина правила Бленда) - это ничего не меняет
    в невырожденных задачах, но нужно для гарантии остановки.
    Если положительных коэффициентов нет - задача неограничена, возвращаем -1.
    """
    min_ratio = float("inf")
    row = -1
    for i, a_row in enumerate(table):
        if a_row[col] > 1e-9:
            ratio = b_col[i] / a_row[col]
            if ratio < min_ratio - 1e-9:
                min_ratio = ratio
                row = i
            elif abs(ratio - min_ratio) <= 1e-9 and basis is not None and basis[i] < basis[row]:
                row = i
    return row


def _build_main_p_row(c_ext, basis, table, b_col, free_cols):
    """
    Строим строку p_j для основной задачи.

    Базисная переменная x[basis[i]] выражается через свободные так:
    x[basis[i]] = b[i] - сумма(table[i][j] * x[free_cols[j]])

    Подставляем это в целевую функцию W = сумма(c[k]*x[k]) и собираем
    коэффициенты при каждой свободной переменной - это и будут p_j.
    Свободный член получившегося выражения - это Q, а в таблице по
    методичке в столбце b строки p_j хранится -Q.
    """
    n_free = len(free_cols)
    m = len(table)

    p_row = [c_ext[free_cols[j]] for j in range(n_free)]
    for j in range(n_free):
        for i in range(m):
            p_row[j] -= c_ext[basis[i]] * table[i][j]

    Q = 0.0
    for i in range(m):
        Q += c_ext[basis[i]] * b_col[i]

    p_b_val = -Q
    return p_row, p_b_val


def _remove_degenerate_art(table, b_col, basis, free_cols, art_set, var_names, output):
    """
    После вспомогательной задачи некоторые искусственные переменные могут
    остаться в базисе со значением 0 - это вырожденный случай.

    Для каждой такой строки пробуем выполнить пивот на ненулевой элемент
    из столбцов настоящих переменных, чтобы вытолкнуть искусственную.
    Если подходящего элемента нет, строка линейно зависима от остальных -
    просто удаляем её.
    """
    rows_to_delete = []
    for i, bi in enumerate(basis):
        if bi not in art_set:
            continue
        if abs(b_col[i]) > 1e-9:
            continue
        pivot_col = -1
        for jj, j in enumerate(free_cols):
            if j not in art_set and abs(table[i][jj]) > 1e-9:
                pivot_col = jj
                break
        if pivot_col != -1:
            entering = free_cols[pivot_col]
            leaving = basis[i]
            if output:
                print(f"Выталкиваем {var_names[leaving]} из базиса строки {i+1}, вводим {var_names[entering]}")
            free_cols[pivot_col] = leaving
            basis[i] = entering
            p_dummy = [0.0] * len(free_cols)
            table, b_col, p_dummy, _ = _pivot_with_b(table, b_col, p_dummy, 0.0, i, pivot_col)
        else:
            rows_to_delete.append(i)
            if output:
                print(f"Строка {i+1} линейно зависима, удаляем её из задачи")
    for i in sorted(rows_to_delete, reverse=True):
        table.pop(i)
        b_col.pop(i)
        basis.pop(i)
    return table, b_col, basis


def _solve_auxiliary(canon: CanonicalProblem, output=True):
    """
    Строим и решаем вспомогательную задачу, чтобы найти начальный базис
    для строк, где его не удалось выделить сразу.
    """
    m = len(canon.A_ext)
    n = canon.n_total

    art_rows = [i for i, bi in enumerate(canon.basis) if bi == -1]
    n_art = len(art_rows)

    A_aug = [list(row) for row in canon.A_ext]
    for row in A_aug:
        row += [0.0] * n_art

    b_col = list(canon.b)
    n_aug = n + n_art
    var_names = list(canon.var_names) + [f"x{n + k + 1}" for k in range(n_art)]

    basis = list(canon.basis)
    art_idx = []
    for k, i in enumerate(art_rows):
        col_art = n + k
        A_aug[i][col_art] = 1.0
        basis[i] = col_art
        art_idx.append(col_art)

    free_cols = [j for j in range(n_aug) if j not in basis]
    table = [[A_aug[i][j] for j in free_cols] for i in range(m)]

    # строка p_j для вспомогательной задачи считается по формуле из методички:
    # p_j = -сумма a_ij по строкам с искусственными переменными,
    # а в столбце b стоит -сумма b_i по тем же строкам
    p_row = [0.0] * len(free_cols)
    p_b_val = 0.0
    for i in art_rows:
        for jj, j in enumerate(free_cols):
            p_row[jj] -= A_aug[i][j]
        p_b_val -= b_col[i]

    if output:
        print_separator("Вспомогательная задача")
        print(f"Искусственные переменные: {[var_names[j] for j in art_idx]}")
        print(f"Начальный базис: {[var_names[j] for j in basis]}")
        print_table(table, b_col, p_row, p_b_val,
                    [var_names[j] for j in free_cols],
                    [var_names[j] for j in basis], iteration=0)

    iteration = 1
    bland = False
    while True:
        if iteration > MAX_ITERATIONS:
            raise RuntimeError("Превышено число итераций во вспомогательной задаче.")
        col_local = _choose_pivot_col(p_row, free_cols, bland)
        if col_local == -1:
            break

        row = _choose_pivot_row(table, b_col, col_local, basis)
        if row == -1:
            raise RuntimeError("Вспомогательная задача неограничена, проверьте исходные данные.")

        # если разрешающая строка имеет b = 0, шаг вырожденный: вершина не меняется,
        # и возможен цикл - до выхода из вырожденности выбираем столбец по Бленду
        bland = abs(b_col[row]) < 1e-9

        entering = free_cols[col_local]
        free_cols[col_local] = basis[row]
        basis[row] = entering

        table, b_col, p_row, p_b_val = _pivot_with_b(table, b_col, p_row, p_b_val, row, col_local)

        if output:
            print_table(table, b_col, p_row, p_b_val,
                        [var_names[j] for j in free_cols],
                        [var_names[j] for j in basis], iteration=iteration)
        iteration += 1

    # по методичке в столбце b строки p_j стоит -W', значит W' = -p_b_val
    W_aux = -p_b_val
    success = abs(W_aux) < 1e-9

    if output:
        if success:
            print(f"\nВспомогательная задача решена, W' = 0.")
            print(f"Базис для основной задачи: {[var_names[j] for j in basis]}")
        else:
            print(f"\nW' = {W_aux:.6g}, это больше нуля.")
            print("Область допустимых решений пуста, у задачи нет решений.")

    # искусственные переменные больше не нужны, убираем их столбцы
    art_set = set(art_idx)
    # обрабатываем вырожденный случай: искусственная переменная осталась в базисе со значением 0
    table, b_col, basis = _remove_degenerate_art(table, b_col, basis, free_cols, art_set, var_names, output)
    keep = [jj for jj, j in enumerate(free_cols) if j not in art_set]
    table_clean = [[row[jj] for jj in keep] for row in table]
    free_cols_clean = [free_cols[jj] for jj in keep]

    return table_clean, b_col, basis, free_cols_clean, var_names, success


def _solve_main(canon: CanonicalProblem, table, b_col, basis, free_cols, var_names, output=True):
    """
    Решает основную задачу, когда начальный базис уже известен.
    """
    p_row, p_b_val = _build_main_p_row(canon.c_ext, basis, table, b_col, free_cols)

    if output:
        print_separator("Основная задача")
        print_table(table, b_col, p_row, p_b_val,
                    [var_names[j] for j in free_cols],
                    [var_names[j] for j in basis], iteration=0)

    iteration = 1
    bland = False
    while True:
        if iteration > MAX_ITERATIONS:
            raise RuntimeError("Превышено число итераций в основной задаче.")
        col_local = _choose_pivot_col(p_row, free_cols, bland)
        if col_local == -1:
            break

        row = _choose_pivot_row(table, b_col, col_local, basis)
        if row == -1:
            return {"feasible": True, "bounded": False}

        # вырожденный шаг (b = 0) - включаем правило Бленда до выхода из вырожденности
        bland = abs(b_col[row]) < 1e-9

        entering = free_cols[col_local]
        free_cols[col_local] = basis[row]
        basis[row] = entering

        table, b_col, p_row, p_b_val = _pivot_with_b(table, b_col, p_row, p_b_val, row, col_local)

        if output:
            print_table(table, b_col, p_row, p_b_val,
                        [var_names[j] for j in free_cols],
                        [var_names[j] for j in basis], iteration=iteration)
        iteration += 1

    n_orig = canon.n_original
    x_vals = [0.0] * n_orig
    for i, bi in enumerate(basis):
        if bi < n_orig:
            x_vals[bi] = b_col[i]

    # в столбце b строки p_j хранится -W_min, поэтому W_min = -p_b_val
    W_min = -p_b_val

    if canon.goal == "max":
        Z_opt = -W_min
    else:
        Z_opt = W_min

    return {
        "feasible": True,
        "bounded": True,
        "x": x_vals,
        "Z": Z_opt,
        "basis": basis,
        "b_col": b_col,
        "var_names": var_names,
    }


def solve(canon: CanonicalProblem, output=True):
    """
    Главная функция решения. Сама решает, нужна ли вспомогательная задача,
    и потом решает основную.
    """
    m = len(canon.A_ext)
    needs_auxiliary = any(bi == -1 for bi in canon.basis)

    if needs_auxiliary:
        table, b_col, basis, free_cols, var_names, success = _solve_auxiliary(canon, output=output)
        if not success:
            return {"feasible": False, "bounded": False}
    else:
        basis = list(canon.basis)
        b_col = list(canon.b)
        var_names = list(canon.var_names)
        free_cols = [j for j in range(canon.n_total) if j not in basis]
        table = [[canon.A_ext[i][j] for j in free_cols] for i in range(m)]

        if output:
            print_separator("Базис найден сразу, вспомогательная задача не нужна")
            print(f"Базис: {[var_names[j] for j in basis]}")

    return _solve_main(canon, table, b_col, basis, free_cols, var_names, output=output)
