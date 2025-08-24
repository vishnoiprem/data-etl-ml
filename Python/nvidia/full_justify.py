def full_justify(words, max_width):
    res = []                # Final result
    line = []               # Words in current line
    ln = 0                  # Total length of words in current line (without spaces)
    i = 0

    while i < len(words):
        w = words[i]
        # Check if current word fits in the line
        # We need: ln + len(w) + (number of spaces) <= max_width
        # Number of spaces = len(line) if we add this word
        if ln + len(w) + len(line) <= max_width:
            line.append(w)
            ln += len(w)
            i += 1
        else:
            # Line is full, justify it
            spaces = max_width - ln  # Total spaces to distribute
            if len(line) == 1:
                # Single word: left-justify with trailing spaces
                res.append(line[0] + ' ' * spaces)
            else:
                # Multiple words: distribute spaces between words
                num_gaps = len(line) - 1
                s, extra = divmod(spaces, num_gaps)  # s = min spaces per gap, extra = leftover
                # Leftmost 'extra' gaps get one additional space
                for j in range(extra):
                    line[j] += ' '
                # Join words with 's' spaces
                res.append((' ' * s).join(line))
            # Reset line
            line, ln = [], 0

    # Handle the last line: left-justified
    last_line = ' '.join(line)
    res.append(last_line + ' ' * (max_width - len(last_line)))

    return res


# ——————————————————————
# ✅ Example Usage
# ——————————————————————

words = ["This", "is", "an", "example", "of", "text", "justification."]
max_width = 16

result = full_justify(words, max_width)

print("Formatted Output:")
for line in result:
    print(f"'{line}'")