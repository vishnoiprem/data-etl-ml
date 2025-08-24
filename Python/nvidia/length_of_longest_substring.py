def length_of_longest_substring(s):
    # Dictionary to store the last index where each character was seen
    last = {}

    # Start of the current window (left pointer)
    start = 0

    # To keep track of the maximum length found so far
    best = 0

    # Iterate through the string with index i and character ch
    for i, ch in enumerate(s):
        # Check if this character has been seen AND is inside the current window
        # (i.e., its last occurrence is at or after 'start')
        if ch in last and last[ch] >= start:
            # Move the start of the window right after the last occurrence
            # This ensures no duplicate in the new window
            start = last[ch] + 1

        # Update the last seen index of this character
        last[ch] = i

        # Update the maximum length if current window is longer
        best = max(best, i - start + 1)

    return best


print(length_of_longest_substring("abcabcbb"))