from gridtree import build
import pytest  # type: ignore


def test_empty_set_results_in_empty_dict():
    assert build(max_leaf_size='does not matter')([]) == {}


def test_1_element_set_results_in_1_element_dict():
    assert build(max_leaf_size=1)([(1,)]) == {(0,): [(1,)]}


def test_2_close_points_result_in_1_leaf_with_leaf_size_2():
    assert build(max_leaf_size=2)([(0.9,), (1,)]) == {(0,): [(0.9,), (1,)]}


def test_3_points_result_in_grid_split_with_leaf_size_2():
    expected = {(0,): {(0,): [(0.4,)], (1,): [(0.9,), (1,)]}}
    assert build(max_leaf_size=2)([(0.4,), (0.9,), (1,)]) == expected


def test_duplication_results_in_recursion_error():
    # That's not quite a feature so feel free to handle this
    # case more gracefully. But I don't want to add significant
    # overheads to solve it.
    with pytest.raises(RecursionError):
        assert build(max_leaf_size=1)([(0.9,), (0.9,), (0.9,)])


def test_points_so_close_they_take_few_levels_to_split():
    expected = {
        (0,): {
            (0,): {(0,): [(0.2,)], (1,): [(0.3,), (0.4,)]},
            (1,): {
                (2,): [(0.6,)],
                (3,): {
                    (6,): [(0.8,)],
                    (7,): [(0.9,), (0.95,)],
                },
            },
        }
    }
    inputs = [(0.2,), (0.3,), (0.4,), (0.6,), (0.8,), (0.9,), (0.95,)]
    actual = build(max_leaf_size=2)(inputs)
    assert actual == expected


def test_05_075_and_1_all_belong_to_right_groups():
    inputs = [(0.3,), (0.5,), (0.75,), (1,)]
    expected = {
        (0,): {
            (0,): [(0.3,)],
            (1,): {
                (2,): [(0.5,)],
                (3,): {(6,): [(0.75,)], (7,): [(1,)]},
            },
        }
    }
    actual = build(max_leaf_size=1)(inputs)
    assert actual == expected
