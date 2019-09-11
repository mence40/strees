from Compiler.types import sint, Array
from permutation import config_shuffle, configure_waksman, random_perm, rec_shuffle, shuffle

# Make IDE happy
try:
    from strees_utils import *
except ImportError:
    pass


def default_config_shuffle(values, use_iter=True):
    """Configures waksman network for default shuffle algorithm."""
    # TODO this won't generate consistent permutations if run on different machines; need to seed rand. num. gen
    if use_iter:
        return config_shuffle(len(values), value_type=sint)
    else:
        return configure_waksman(random_perm(len(values)))


def default_shuffle(values, config, reverse=False, use_iter=True):
    """Shuffles values in place using default shuffle algorithm."""
    if use_iter:
        shuffle(values, config=config, value_type=sint, reverse=reverse)
    else:
        rec_shuffle(values, config=config, value_type=sint, reverse=reverse)


def sort_and_permute(key_col, val_col):
    """Sorts and permutes columns."""
    same_len(key_col, val_col)
    if not is_two_pow(len(key_col)):
        raise Exception("Only powers of two supported for shuffles")

    sorted_value_col, order_col = sort_by(key_col, val_col)

    config_bits = default_config_shuffle(key_col)
    default_shuffle(order_col, config=config_bits)

    return sorted_value_col, order_col, config_bits


def open_permute(values, open_perm):
    """Applies a public permutation to an Array of sints."""
    if not isinstance(values, Array):
        raise Exception("Must be array")
    reordered = Array(len(values), sint)
    for idx, val in enumerate(values):
        old_idx = open_perm[idx]
        reordered[idx] = values[old_idx]
    return reordered
