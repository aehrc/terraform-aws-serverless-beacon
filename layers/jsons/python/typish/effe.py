
from typing import Tuple, Type

from typish import instance_of, subclass_of, TypingType

# Kijk hier effe naar:

# # A supertype for types like: list, tuple, set, ... (not str!)
# Aggregation = type('Aggegation', (object, ), {})
#
# # A supertype for types like: List[...], Tuple[...], Set[...]
# GenericAggregation = type('GenericAggregation', (Aggregation,), {})
#
#
# if __name__ == '__main__':
#
#
#
#
#
# print(isinstance(Tuple[int, str], GenericCollectionType))


# def test_is_something_hashable(self):
#     Sequence[Something['attr': int]]  # TODO
#
#
# def test_instance_of_tuple(self):
#     Tuple[type, ...]  # TODO dit dus...


# print( instance_of((1, 2, 3), Tuple[int, ...]) )


# print( subclass_of(Tuple[int, ...], Tuple[int, ...]) )
# print( instance_of(Tuple[int], Type[Tuple[int]]) )
