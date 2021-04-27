from collections import defaultdict
from functools import reduce
from itertools import zip_longest
from operator import ior
from typing import Annotated, Collection
import itertools


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


def _distance_squared(p1, p2):
    return sum((p1_i - p2_i) ** 2 for p1_i, p2_i in zip(p1, p2))


def _iter_points_in_range(points, search_point, radius):
    radius_squared = radius ** 2
    for point in points:
        if _distance_squared(point, search_point) <= radius_squared:
            yield point


def _make_bounding_box(search_point, radius):
    r = radius
    options = [(x_i + r, x_i - r) for x_i in search_point]
    product = tuple(itertools.product(*options))
    return product


def _iter_point_indices(points, level):
    for point in points:
        yield _get_point_index_for_level(point, level)


def _get_point_index_for_level(point, level):
    return tuple(
        int(x_i * (1 << level)) - (x_i == 1)
        for x_i in point
    )


def _get_points_in_bounding_box(tree, bbox, level=0):
    indices = _iter_point_indices(bbox, level)
    indices = set(indices)
    index, = indices
    tree_or_bucket = tree[index]
    if isinstance(tree_or_bucket, dict):
        return _get_points_in_bounding_box(tree_or_bucket, bbox, level + 1)
    else:
        return tree_or_bucket


def find_in_radius(tree, *, search_point, radius):
    bbox = _make_bounding_box(search_point, radius)
    bounded_points = _get_points_in_bounding_box(tree, bbox)
    points_in_range = _iter_points_in_range(
        bounded_points, search_point, radius)
    return tuple(points_in_range)
