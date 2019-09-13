from Compiler.types import sint, Array, MemValue
from library import print_ln, print_str, for_range_parallel, for_range
from util import tree_reduce

MPC_ERROR_FLAG = "MPC_ERROR"
MPC_WARN_FLAG = "MPC_WARN"
DEBUG = False

# Parameter for scaling denominator in GINI index computation
ALPHA = 10


class Acc:
    """Accumulator class that can be used to increment/dec a secret values.

    Can be used inside MP-SPDZ runtime loops."""

    def __init__(self, init_val):
        self.val = MemValue(init_val)

    def inc_by(self, step):
        self.val.write(self.get_val() + step)

    def dec_by(self, step):
        self.val.write(self.get_val() - step)

    def get_val(self):
        return self.val.read()


def debug_only(f):
    def wrapper(*args, **kwargs):
        if DEBUG:
            f(*args, **kwargs)
        return

    return wrapper


def print_list(lst):
    print_str("[ ")
    for v in lst:
        print_str("%s ", v.reveal())
    print_ln("]")


def print_mat(mat):
    print_ln("[ ")
    for row in mat:
        print_str(" ")
        print_list(row)
    print_ln("]")


def alpha_scale(val):
    """Scales value according to ALPHA param."""
    return ALPHA * val + 1


def log_or(bit_a, bit_b):
    """Logical OR via arithmetic ops."""
    return bit_a + bit_b - bit_a * bit_b


def toggle(bit, elements):
    """Keeps elements same if bit is 1, sets all to 0 otherwise"""
    if not isinstance(elements, Array):
        raise Exception("Call this with array")
    return elements * bit


def tree_sum(elements):
    """Computes sum of elements, using MP-SPDZ tree_reduce."""
    return tree_reduce(lambda x, y: x + y, elements)


def pairwise_and(bits_a, bits_b):
    """Pairwise AND of bits."""
    return prod(bits_a, bits_b)


def prod(left, right):
    """Pairwise product of elements."""
    same_len(left, right)
    array_check(left)
    array_check(right)

    num_elements = len(left)
    res = Array(num_elements, sint)

    # @for_range(0, num_elements)
    @for_range_parallel(min(32, num_elements), num_elements)
    def _(i):
        res[i] = left[i] * right[i]

    return res


def neg(bits):
    """Bitwise not of each element in bits (or singleton bit)."""
    if isinstance(bits, sint) or isinstance(bits, int):
        return 1 - bits
    array_check(bits)
    num_elements = len(bits)
    res = Array(num_elements, sint)

    @for_range(0, num_elements)
    def _(i):
        res[i] = 1 - bits[i]

    return res


def lt_threshold(elements, threshold):
    """Compares all values to threshold value and returns result sints."""

    array_check(elements)

    num_elements = len(elements)
    res = Array(num_elements, sint)

    # @for_range(0, num_elements)
    @for_range_parallel(min(32, num_elements), num_elements)
    def _(i):
        res[i] = elements[i] <= threshold

    return res


def array_check(arr):
    if not isinstance(arr, Array):
        raise Exception("Must be Array but was %s" % type(arr))


def same_len(row_a, row_b):
    if len(row_a) != len(row_b):
        raise Exception("Must be same length but was {} and {}".format(len(row_a), len(row_b)))


def if_else_row(bit, row_a, row_b):
    same_len(row_a, row_b)
    return [bit.if_else(a, b) for a, b in zip(row_a, row_b)]


# Largely copied from MP-SPDZ
def default_sort(keys, values, sorted_length=1, n_parallel=32):
    def cond_swap_with_bit(b, x, y):
        bx = b * x
        by = b * y
        return bx + y - by, x - bx + by

    def cond_swap(x, y):
        b = x < y
        x_new, y_new = cond_swap_with_bit(b, x, y)
        return b, x_new, y_new

    l = sorted_length
    while l < len(keys):
        l *= 2
        k = 1
        while k < l:
            k *= 2
            n_outer = len(keys) / l
            n_inner = l / k
            n_innermost = 1 if k == 2 else k / 2 - 1

            @for_range_parallel(n_parallel / n_innermost / n_inner, n_outer)
            def loop(i):
                @for_range_parallel(n_parallel / n_innermost, n_inner)
                def inner(j):
                    base = i * l + j
                    step = l / k
                    print_ln("base %s step %s", base, step)
                    if k == 2:
                        outer_comp_bit, keys[base], keys[base + step] = cond_swap(
                            keys[base], keys[base + step])
                        values[base], values[base + step] = cond_swap_with_bit(
                            outer_comp_bit, values[base], values[base + step])
                    else:
                        @for_range_parallel(n_parallel, n_innermost)
                        def f(i):
                            m1 = step + i * 2 * step
                            m2 = m1 + base
                            inner_comp_bit, keys[m2], keys[m2 + step] = cond_swap(
                                keys[m2], keys[m2 + step])
                            values[m2], values[m2 + step] = cond_swap_with_bit(
                                inner_comp_bit, values[m2], values[m2 + step])


def sort_by(keys, values):
    """Sorts keys and values keys."""
    same_len(keys, values)
    # default_sort has side-effect
    sorted_keys = keys[:]
    sorted_values = values[:]
    default_sort(sorted_keys, sorted_values)
    return sorted_keys, sorted_values


def mat_assign_op(raw_mat, f):
    if len(raw_mat) == 0:
        raise Exception("Empty matrix")
    if not raw_mat[0]:
        raise Exception("Empty matrix")
    num_rows = len(raw_mat)
    num_cols = len(raw_mat[0])

    mat = []
    for r in range(num_rows):
        row = []
        for c in range(num_cols):
            row.append(f(raw_mat[r][c]))
        mat.append(row)
    return mat


def reveal_mat(mat):
    """Reveals matrix of sints.

    TODO probably already exists somewhere
    TODO use Matrix?
    """
    return mat_assign_op(mat, lambda x: x.reveal())


def input_matrix(mat):
    """Inputs matrix of ints into MPC.

    TODO probably already exists somewhere
    TODO use Matrix?
    """
    return mat_assign_op(mat, lambda x: sint(x))


def get_col(rows, col_idx):
    """Returns column at index as list."""
    return Array.create_from(row[col_idx] for row in rows)


def reveal_list(lst):
    """Reveals list of sints.

    TODO probably already exists somewhere.
    """
    if not isinstance(lst, Array):
        raise Exception("Must be array")
    return [val for val in lst.reveal()]


def input_list(lst):
    """Inputs list of values into MPC."""
    return Array.create_from(sint(val) for val in lst)


def to_col_arrays(rows):
    """Converts rows to list of arrays representing columns."""
    if not rows or not rows[0]:
        raise Exception("Can't call this with empty matrix")
    n = len(rows)
    columns = [Array(n, sint) for _ in rows[0]]
    for row_idx, row in enumerate(rows):
        for col_idx, val in enumerate(row):
            columns[col_idx][row_idx] = val
    return columns


def transpose(mat):
    """Transposes matrix."""
    if not mat:
        return []
    if not mat[0]:
        return []
    columns = [[] for _ in mat[0]]
    for row in mat:
        for idx, val in enumerate(row):
            columns[idx].append(val)
    return columns


def is_two_pow(n):
    """True if 2 power.

    Lazily stolen from SO: https://stackoverflow.com/questions/57025836/check-if-a-given-number-is-power-of-two-in
    -python."""
    return (n & (n - 1) == 0) and n != 0
