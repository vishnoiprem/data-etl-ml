"""
Design HashMap - Bucket class
This represents one bucket in the hash map that handles collisions via chaining.
"""


class Bucket:
    def __init__(self):
        self.bucket = []

    def get(self, key):
        """
        Find key in this bucket.
        Returns (index, value) if found, (-1, -1) if not.
        """
        for i, (k, v) in enumerate(self.bucket):
            if k == key:
                return (i, v)
        return (-1, -1)

    def update(self, key, value):
        """
        Insert or update key-value pair in this bucket.
        """
        i, _ = self.get(key)
        if i == -1:
            self.bucket.append([key, value])
        else:
            self.bucket[i][1] = value

    def remove(self, key):
        """
        Remove key from this bucket if it exists.
        """
        i, _ = self.get(key)
        if i != -1:
            self.bucket.pop(i)
