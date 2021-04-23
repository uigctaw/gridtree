from collections import defaultdict
from functools import reduce
from itertools import zip_longest
from operator import ior
from typing import Annotated, Collection


def ValueRange(left, right, *, right_inclusive=False):
    """It exists just to annotate a type."""

    def is_valid(value):
        return left <= value < right or right_inclusive and value == right

    return is_valid


def Unique():
    """It exists just to annotate a type."""

    def is_valid(value):
        return len(value) == len(set(value))

    return is_valid


def GreaterThanEqual(threshold):
    """It exists just to annotate a type."""

    def is_valid(value):
        return value >= threshold

    return is_valid


NormalizedFloat = Annotated[float, ValueRange(0, 1, right_inclusive=True)]
PositiveInteger = Annotated[int, GreaterThanEqual(1)]


def build(*, max_leaf_size: PositiveInteger):

    def _gtree(
            points,
            level,
            parent_index,
            ):

        if len(points) <= max_leaf_size:
            return points

        index_to_points = defaultdict(list)

        for point in points:
            index = tuple(
                (p_i << 1) + (x_i * (1 << level) >= p_i + 0.5)
                for x_i, p_i in zip(point, parent_index)
            )
            index_to_points[index].append(point)

        index_to_node = {}
        for index, node_points in index_to_points.items():
            index_to_node[index] = _gtree(
                    points=node_points,
                    level=level + 1,
                    parent_index=index,
                    )

        return index_to_node

    def gtree(
            points: Annotated[
                Collection[tuple[NormalizedFloat, ...]],
                Unique,
            ],
    ):
        """

        Raises
        ------
        RecursionError: If duplicate points don't fit in a leaf node.
        """
        if points:
            reference_point = next(iter(points))
            parent_index = (0,) * len(reference_point)
            return {
                parent_index: _gtree(
                    points, parent_index=parent_index, level=0)
                }
        else:
            return {}

    return gtree


def build_list(*, max_leaf_size: PositiveInteger):
    builder = build(max_leaf_size=max_leaf_size)

    def _gtree_to_list(tree):
        if not tree:
            return []
        if isinstance(tree, list):
            return tree

        the_list = [tree]
        sub_lists = [
                _gtree_to_list(v)
                for v in tree.values()
                if isinstance(v, dict)
        ]
        for next_list_element_parts in zip_longest(*sub_lists):
            next_element = reduce(
                    ior,
                    filter(None, next_list_element_parts),
                    {},
                    )
            the_list.append(next_element)
        return the_list

    def gtree_to_list(
            points: Annotated[
                Collection[tuple[NormalizedFloat, ...]],
                Unique,
            ],
    ):
        tree = builder(points=points)
        the_list = _gtree_to_list(tree)
        return the_list

    return gtree_to_list


def find_closest(calculate_distance):

    def _find_closest(search_point, tree):
        if isinstance(tree, dict):
            return _find_closest_in_tree(
                    search_point, tree, calculate_distance)
        else:
            return _find_closest_in_list(
                    search_point, tree, calculate_distance)

    return _find_closest


def _find_closest_in_tree(search_point, tree, calculate_distance):
    if not tree:
        return None

    this_level = 0
    index_for_this_level = _calculate_index_for_level(search_point, this_level)
    tree_or_bucket = tree
    while True:
        try:
            if isinstance(tree_or_bucket, dict):
                tree_or_bucket = tree_or_bucket[index_for_this_level]
            else:
                return _find_closest_in_bucket(
                        search_point, tree_or_bucket, calculate_distance)
        except KeyError:
            pass
  

def _calculate_index_for_level(search_point, level):
    return tuple(
        int((1 << level) * x_i) - (x_i == 1)
        for x_i in search_point
    )


def _find_closest_in_bucket(search_point, bucket, calculate_distance):
    if len(bucket) == 1:  # len 0 does not make sense
        closest, = bucket
        return closest

    p1, *tail = bucket
    min_distance_so_far = calculate_distance(search_point, p1)

    if min_distance_so_far == 0:
        return p1

    closest_point_so_far = p1

    for p in tail:
        distance = calculate_distance(search_point, p)
        if distance < min_distance_so_far:
            min_distance_so_far = distance
            closest_point_so_far = p

        if min_distance_so_far == 0:
            return closest_point_so_far

    return closest_point_so_far 
