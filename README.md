# gridtree
Generalized quadtree.


# Installation
```
pip install gridtree
```

# Usage

TODO: expand

```python
points : Collection[tuple[NormalizedFloat, ...]] # between 0 and 1 inclusive

tree = GTree(max_leaf_size=2)(points)
tree_as_list = GTreeList(max_leaf_size=2)(points)
tree_as_list = GTreeList.gtree_to_list(tree)
```

# Examples

TODO

