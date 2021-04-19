from collections import defaultdict
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
