# model.py - классы для хранения данных задачи линейного программирования.

from dataclasses import dataclass
from typing import List


@dataclass
class LPProblem:
    """
    Исходная задача, как её ввёл пользователь.

    n_vars - количество переменных x1...xn
    c      - коэффициенты целевой функции
    goal   - 'max' или 'min'
    A      - матрица коэффициентов ограничений
    b      - правые части ограничений
    signs  - знак каждого ограничения: '<=', '=' или '>='
    """
    n_vars: int
    c: List[float]
    goal: str
    A: List[List[float]]
    b: List[float]
    signs: List[str]


@dataclass
class CanonicalProblem:
    """
    Задача после приведения к каноническому виду.
    Целевая функция переведена в min, все ограничения - равенства,
    все b положительные.

    c_ext      - коэффициенты целевой функции для всех переменных
    A_ext      - расширенная матрица ограничений (с доп. переменными)
    b          - правые части
    n_original - сколько было переменных в исходной задаче
    n_total    - сколько переменных стало после добавления доп. переменных
    var_names  - имена всех переменных, например x1, x2, x3...
    basis      - индексы базисных переменных по каждой строке,
                 если базис найти не удалось, стоит -1
    goal       - исходный тип задачи (нужно чтобы потом правильно вывести Z)
    """
    c_ext: List[float]
    A_ext: List[List[float]]
    b: List[float]
    n_original: int
    n_total: int
    var_names: List[str]
    basis: List[int]
    goal: str
