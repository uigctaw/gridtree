from gridtree import build, build_list, find_closest
import pytest  # type: ignore
import random


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


def test_2d_case():
    inputs = [
            (0.25, 0.25), (0.4, 0.6), (0.3, 1),
            (0.5, 0.5), (0.75, 0.75), (1, 1),
            ]
    expected = {
        (0, 0): {
            (0, 0): [(0.25, 0.25)],
            (0, 1): [(0.4, 0.6), (0.3, 1)],
            (1, 1): {
                (2, 2): [(0.5, 0.5)],
                (3, 3): [(0.75, 0.75), (1, 1)],
            },
        }
    }
    actual = build(max_leaf_size=2)(inputs)
    assert actual == expected


class TestTreeAsList:

    def test_empty_set_results_in_empty_list(self):
        assert build_list(max_leaf_size='does not matter')([]) == []

    def test_1_element_set_results_in_1_element_list(self):
        assert build_list(max_leaf_size=1)([(1,)]) == [{(0,): [(1,)]}]

    def test_2_close_points_with_leaf_size_2_result_in_1_element_list(self):
        actual = build_list(max_leaf_size=2)([(0.9,), (1,)])
        assert actual == [{(0,): [(0.9,), (1,)]}]

    def test_3_points_result_in_2_element_list(self):
        lvl1 = {(0,): [(0.4,)], (1,): [(0.9,), (1,)]}
        expected = [{(0,): lvl1}, lvl1]
        actual = build_list(max_leaf_size=2)([(0.4,), (0.9,), (1,)])
        assert actual == expected

    def test_points_so_close_they_result_in_many_element_list(self):
        lvl3 = {
            (6,): [(0.8,)],
            (7,): [(0.9,), (0.95,)],
        }
        lvl2_0 = {
            (0,): [(0.2,)],
            (1,): [(0.3,), (0.4,)],
        }
        lvl2_1 = {
            (2,): [(0.6,)],
            (3,): lvl3,
        }
        lvl1 = {
            (0,): lvl2_0,
            (1,): lvl2_1,
        }
        expected = [
            {(0,): lvl1},
            lvl1,
            lvl2_0 | lvl2_1,
            lvl3,
        ]

        inputs = [(0.2,), (0.3,), (0.4,), (0.6,), (0.8,), (0.9,), (0.95,)]
        actual = build_list(max_leaf_size=2)(inputs)
        assert actual == expected


def calculate_distance(p1, p2):
    return sum((x_i1 - x_i2) ** 2 for x_i1, x_i2 in  zip(p1, p2))


find_closest = find_closest(calculate_distance)


class TestPointSearch:

    def test_find_closest_point_if_there_are_no_points(self):
        point = (0.5,)
        tree = {}
        assert find_closest(point, tree) is None

    def test_find_closest_finds_coincident_point__1_point_in_total(self):
        point = (0.5,)
        tree = {(0,): [(0.5,)]}
        assert find_closest(point, tree) == (0.5,)

    def test_find_closest_finds_nearby_point__1_point_in_total(self):
        point = (random.random(),)
        existing_point = (random.random(),)
        tree = {(0,): [existing_point]}
        assert find_closest(point, tree) == existing_point

    def test_find_closest_finds_the_closest_out_of_few(self):
        x1, x2 = search_point = (0.25, 0.25)
        closest = (x1 + random.random() / 10, x2 + random.random() / 10)
        tree = {(0, 0): [(0, 0), closest, (0.5, 0.5), (1, 1)]}
        assert find_closest(search_point, tree) == closest

    @pytest.mark.skip('TODO')
    def test_find_closest_on_not_a_first_level(self):
        pass

    @pytest.mark.skip('TODO')
    def test_find_closest_for_search_point_on_right_border(self):
        pass

    @pytest.mark.skip('TODO')
    def test_find_closest_if_closest_is_in_nearby_cell_on_the_same_level(self):
        pass

    @pytest.mark.skip('TODO')
    def test_find_closest_if_closest_is_in_nearby_cell_on_higher_level(self):
        pass

    @pytest.mark.skip('TODO')
    def test_find_closest_if_closest_is_in_nearby_cell_on_lower_level(self):
        pass
