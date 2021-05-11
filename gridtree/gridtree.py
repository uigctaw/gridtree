from collections import defaultdict
from functools import reduce
from itertools import zip_longest
from operator import ior
from typing import Collection
import itertools
import math


class PositiveInt(int):

    def __new__(cls, value):
        val = super().__new__(cls, value)
        if val > 0:
            return val
        else:
            raise ValueError(f'Not greater than 0: `{val}`')


class NormalizedFloat(float):

    def __new__(cls, value):
        val = super().__new__(cls, value)
        if 0 <= val <= 1:
            return val
        else:
            raise ValueError(f'Not btetween 0 and 1 (inclusive): `{val}`')


class GTree:

    def __init__(self, max_leaf_size: PositiveInt):
        self._max_leaf_size = PositiveInt(max_leaf_size)

    def __repr__(self):
        return f'Gtree(max_leaf_size={self._max_leaf_size})'

    def _gtree(
            self,
            points,
            level,
            parent_index,
            ):

        if len(points) <= self._max_leaf_size:
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
            index_to_node[index] = self._gtree(
                    points=node_points,
                    level=level + 1,
                    parent_index=index,
                    )

        return index_to_node

    def __call__(self, points: Collection[tuple[NormalizedFloat, ...]]):
        """Build a `gridtree`: n-dimensional quadtree.

        Raises
        ------
        RecursionError:
            If duplicate points don't fit in a leaf node.
            The passed points should not have duplicates!
            No check is being made.
        """
        if points:
            reference_point = next(iter(points))
            parent_index = (0,) * len(reference_point)
            return {
                parent_index: self._gtree(
                    points, parent_index=parent_index, level=0)
                }
        else:
            return {}


class GTreeList:

    def __init__(self, *, max_leaf_size: PositiveInt):
        self._gtree = GTree(max_leaf_size=max_leaf_size)

    @classmethod
    def gtree_to_list(cls, tree):
        if not tree:
            return []
        if isinstance(tree, list):
            return tree

        the_list = [tree]
        sub_lists = [
                cls.gtree_to_list(v)
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

    def __call__(self, points: Collection[tuple[NormalizedFloat, ...]]):
        tree = self._gtree(points=points)
        the_list = self.gtree_to_list(tree)
        return the_list


def _distance_squared(p1, p2):
    return sum((p1_i - p2_i) ** 2 for p1_i, p2_i in zip(p1, p2))


def _iter_points_in_range(points, search_point, radius):
    radius_squared = radius ** 2
    for point in points:
        if _distance_squared(point, search_point) <= radius_squared:
            yield point


def _reduce_bbox(bbox, index, level):
    cell_width = 1 / (1 << level)
    low_cell = tuple(i * cell_width for i in index)
    high_cell = tuple(x_i + cell_width for x_i in low_cell)
    low_bbox, high_bbox = bbox
    if low_cell > high_bbox:
        return None
    else:
        return (
            tuple(max(x_i1, x_i2) for x_i1, x_i2 in zip(low_cell, low_bbox)),
            tuple(min(x_i1, x_i2) for x_i1, x_i2 in zip(high_cell, high_bbox)),
        )


def _get_point_index_for_level(point, level):
    return tuple(
        int(x_i * (1 << level)) - (x_i == 1)
        for x_i in point
    )


def _iter_points_in_bounding_box(bbox, tree, level):
    for index, tree_or_bucket in tree.items():
        if isinstance(tree_or_bucket, list):
            for point in tree_or_bucket:
                yield point
        else:
            reduced_bbox = _reduce_bbox(bbox, index, level)
            if reduced_bbox:
                for point in _iter_points_in_bounding_box(
                        reduced_bbox,
                        tree_or_bucket,
                        level + 1,
                        ):
                    yield point


def _calculate_level(length):
    inverse = math.ceil(1 / length)
    shifts = 0
    while inverse:
        inverse >>= 1
        shifts += 1
    return shifts


def _iter_points_in_bounding_box_in_list_tree(bbox, list_tree):
    lengths = [(bi - ai) for ai, bi in zip(*bbox)]
    potential_level = _calculate_level(max(lengths))
    init_level = max(min(potential_level, len(list_tree)) - 1, 0)
    ids_along_each_dimension = [
        tuple(range(
            int(ai * (num_sections := (1 << init_level))),
            int(bi * num_sections) + (bi < 1),
            ))
        for ai, bi in zip(*bbox)
    ]
    indices_to_search = list(itertools.product(*ids_along_each_dimension))
    indices_to_bboxes = {
            index_: _reduce_bbox(bbox, index_, init_level)
            for index_ in indices_to_search
            }

    init_indices_to_actual_indicies = {}
    for init_index in indices_to_search:
        index = init_index
        level = init_level
        while True:
            tree = list_tree[level]
            if index in tree:
                init_indices_to_actual_indicies[init_index] = (index, level)
                break
            else:
                index = tuple(xi // 2 for xi in index)
                level -= 1

    for init_index, bbox in indices_to_bboxes.items():
        index, level = init_indices_to_actual_indicies[init_index]
        tree_or_bucket = list_tree[level][index]
        if isinstance(tree_or_bucket, list):
            for point in tree_or_bucket:
                yield point
        else:
            for point in _iter_points_in_bounding_box(
                    bbox, tree_or_bucket, level + 1):
                yield point


def find_in_radius(tree_or_list_tree, *, search_point, radius):
    bounding_box = tuple(zip(*(
        (x - radius, x + radius)
        for x in search_point
    )))
    if isinstance(tree_or_list_tree, dict):
        bounded_points = _iter_points_in_bounding_box(
                bounding_box,
                tree=tree_or_list_tree,
                level=0,
                )
    else:
        bounded_points = _iter_points_in_bounding_box_in_list_tree(
                bounding_box,
                list_tree=tree_or_list_tree,
                )
    points_in_range = _iter_points_in_range(
        bounded_points, search_point, radius)
    return tuple(points_in_range)
