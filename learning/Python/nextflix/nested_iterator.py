from nested_integers import NestedIntegers


class NestedIterator:
    # Initializes the NestedIterator with nested_list
    def __init__(self, nested_list):
        # Write your code here
        pass

    # checks if there are still some integers in nested_list
    def has_next(self):
        # Write your code here
        pass

    # returns the next element from nested_list
    def next(self):
        # Write your code here
        pass


# ------ Please don't change the following function ----------
# flatten_list function is used for testing porpuses.
# Your code will be tested using this function
def flatten_list(nested_iterator_object):
    result = []
    while nested_iterator_object.has_next():
        result.append(nested_iterator_object.next())
    return result