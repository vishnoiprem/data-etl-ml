ow
to
Approach
3
Sum in an
Interview(Step
by
Step)

Step
1: Understand
the
Problem(30
seconds)

You
're given an array. Find all unique triplets that sum to zero.

nums = [-1, 0, 1, 2, -1, -4]
Output: [[-1, -1, 2], [-1, 0, 1]]

Step
2: Ask
Clarifying
Questions(30
seconds)

- "Should the triplets be unique?" → YES(no
duplicates)
- "What order should the output be in?" → Any
order is fine
- "Can the array have negatives, zeros, positives?" → YES

Step
3: Start
With
Brute
Force(Show
You
Can
Think)

# O(n³) - check every triplet
for i in range(n):
    for j in range(i + 1, n):
        for k in range(j + 1, n):
            if nums[i] + nums[j] + nums[k] == 0:
        # save it

Say: "This works but is O(n³). Can we do better?"

Step
4: Think
Out
Loud(This is what
interviewers
want!)

Key
insight: If
I
fix
nums[i], the
problem
becomes
2
Sum:
▎ "Find two numbers that sum to -nums[i]"

And
we
already
know
2
Sum
can
be
solved in O(n)
with two pointers!

Step
5: Build
the
Solution

Step
5
a: Sort
the
array
first

nums.sort()

Why? Two
pointers
only
works
on
sorted
arrays.

Step
5
b: Fix
one
number, use
two
pointers
for the other two

for i in range(len(nums) - 2):
    left = i + 1
    right = len(nums) - 1

    while left < right:
        total = nums[i] + nums[left] + nums[right]

        if total == 0:
        # found a triplet!
        elif total < 0:
            left += 1  # sum too small, increase it
        else:
            right -= 1  # sum too big, decrease it

Step
5
c: Handle
duplicates

The
trickiest
part.After
finding
a
triplet, skip
duplicates:

# Skip duplicate first numbers
if i > 0 and nums[i] == nums[i - 1]:
    continue

# Skip duplicate left pointers after match
while left < right and nums[left] == nums[left + 1]:
    left += 1

# Skip duplicate right pointers after match
while left < right and nums[right] == nums[right - 1]:
    right -= 1

Step
6: Full
Clean
Solution


def three_sum(nums):
    nums.sort()
    result = []

    for i in range(len(nums) - 2):
        # Skip duplicate first numbers
        if i > 0 and nums[i] == nums[i - 1]:
            continue

        left, right = i + 1, len(nums) - 1

        while left < right:
            total = nums[i] + nums[left] + nums[right]

            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1

                # Skip duplicates
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1

            elif total < 0:
                left += 1
            else:
                right -= 1

    return result


Step
7: Walk
Through
an
Example(Talk
While
You
Code!)

nums = [-1, 0, 1, 2, -1, -4]
After
sort: [-4, -1, -1, 0, 1, 2]

i = 0, num = -4:
l = 1, r = 5: -4 + -1 + 2 = -3 → l + +
l = 2, r = 5: -4 + -1 + 2 = -3 → l + +
l = 3, r = 5: -4 + 0 + 2 = -2 → l + +
l = 4, r = 5: -4 + 1 + 2 = -1 → l + +
No
pair
found

i = 1, num = -1:
l = 2, r = 5: -1 + -1 + 2 = 0 ✓ → [-1, -1, 2]
l = 3, r = 4: -1 + 0 + 1 = 0 ✓ → [-1, 0, 1]

i = 2: skip(duplicate
of
i = 1)

i = 3, num = 0:
l = 4, r = 5: 0 + 1 + 2 = 3 → r - -
No
pair

Result: [[-1, -1, 2], [-1, 0, 1]] ✓

What
to
Say in the
Interview

Opening:
▎ "I'll use a two-pointer approach after sorting. For each number, I'll look for two others that sum to its negative using two pointers."

While
coding:
▎ "I'll skip duplicates here to avoid repeated triplets."

After
coding:
▎ "Let me trace through an example to verify... The time complexity is O(n²) since for each of n elements, we do an O(n) two-pointer search."

Cheat
Sheet
to
Memorize

┌──────┬──────────────────────────────┬──────────────────────┐
│ Step │             What             │         Why          │
├──────┼──────────────────────────────┼──────────────────────┤
│ 1    │ nums.sort()                  │ enables
two
pointers │
├──────┼──────────────────────────────┼──────────────────────┤
│ 2    │ Fix
i, move
l and r          │ turns
3
sum
into
2
sum │
├──────┼──────────────────────────────┼──────────────────────┤
│ 3    │ total == 0 → save, move
both │ found
answer         │
├──────┼──────────────────────────────┼──────────────────────┤
│ 4    │ total < 0 → l + +              │ need
bigger
sum      │
├──────┼──────────────────────────────┼──────────────────────┤
│ 5    │ total > 0 → r - -              │ need
smaller
sum     │
├──────┼──────────────────────────────┼──────────────────────┤
│ 6    │ Skip
duplicates              │ avoid
repeats        │
└──────┴──────────────────────────────┴──────────────────────┘

Complexity: O(n²) time, O(1)
extra
space(excluding
output) 💡