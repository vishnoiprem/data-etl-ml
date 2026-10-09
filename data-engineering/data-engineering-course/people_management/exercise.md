# Capstone Exercise — Build Your Own People Management Question Bank

> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <prem.vishnoi@example.com>

This is the capstone for the People Management track. By the
end of it, you should have a **20-30 question personal question
bank** with worked answers, ready to deploy in any People
Management round.

Time: 6-10 hours over 2-3 weeks. Do it in 3 phases.

---

## Phase 1 — Mine the canonical questions (2-3 hours)

Open `docs/reference/em_interview_canonical_questions.md`.
Read all 22 People Management questions and the 131 Behavioral
questions. For each, ask: **could I be asked this in a
People Management round?** If yes, add it to a candidate list.

Target: 30-40 candidate questions.

For each candidate, tag it with:
- **Category** (managing down / up / sideways / self / crisis)
- **Rubric row** (people growth / performance mgmt / execution /
  influence / self-awareness / hiring)
- **Current answer in my bank** (yes / no / partial)

The output is a coverage matrix:

```
                       In bank  Partial  Missing
Managing down            3        2         1
Managing up              1        1         1
Managing sideways        2        1         1
Managing self            1        0         1
Crisis                   0        1         1
```

The "missing" column is your prep priority for Phase 2.

---

## Phase 2 — Write the missing stories (3-5 hours)

For each missing category, write 1-2 new stories. Use the
template from Lesson 02:

```
TITLE: [One-line name]
CATEGORY: [Managing down / Managing up / etc]
QUESTION(S) IT ANSWERS: [2-3 specific questions]
RUBRIC ROW: [People growth / Performance mgmt / etc]
THE PERSON: [2-3 sentences on who they were at the start]
THE STORY (90-120 sec spoken):
[Write it out as you'd say it]
THE NUMBER: [The 1-2 numbers that anchor the impact]
THE TAKEAWAY: [One sentence, the beat you end on]
FOLLOW-UP I'LL PROBE FIRST: [The follow-up I want them to ask]
```

Each story should pass the 8 quality tests from Lesson 02:
- The 5-question "so what" test (4+/5)
- Names a specific person
- Describes before/after
- Speaks in 90-120 seconds
- Has a specific number
- Doesn't blame anyone
- Ends on a beat about the person
- Would I tell this in front of the person?

Target: 20-25 stories total (combining the 12-15 from
Lesson 02 with the new 5-10 from this phase).

---

## Phase 3 — Rehearse and refine (2-3 hours)

For each story in the bank:

1. **Time yourself telling it out loud.** Target 90-120
   seconds. If it's over, tighten. If it's under, add the
   specific person.
2. **Practice with the 5-question "so what" test.** For
   each story, the interviewer might ask:
   - "What would you do differently next time?"
   - "How do you know that worked?"
   - "What did [the other person] take away?"
   - "What would you tell a new EM about this situation?"
   - "What's the transferable lesson?"

   Have a 30-60 second answer for each.
3. **Practice the reverse-interview questions** (from
   `behavioral_interviews/04_mock_interviews_and_analyses/02_mock_meta.md`).
   Have 3 questions ready that signal senior thinking.
4. **Run a mock with a friend.** 45 minutes, 6 questions.
   Have your friend pick from your bank. Listen to the
   feedback.

---

## Deliverable

At the end of the 3 phases, you should have:

- A 20-25 story EM bank, organized by category, with
  worked 90-120 second answers
- 5-question "so what" answers for each story
- 3 reverse-interview questions ready
- One recorded mock with a friend, with self-critique

That's the full People Management interview prep. The
remaining 80% is reps — the more you tell the stories
out loud, the more naturally they come in the actual
interview.

---

## The 22 canonical People Management questions (from the
spine)

For reference, here are all 22 PM questions from
`docs/reference/em_interview_canonical_questions.md`, in the
order they appear in the spine:

1. Tell me about a time you had a conflict with someone. How
   did you resolve it and what did you learn?
2. How would you handle an engineer who creates conflict with
   team members but is still performing well?
3. Why did you choose Engineering Manager as a career path?
4. Tell me about a time when you dealt with a conflict with
   engineers.
5. Tell me about a time when you had a disagreement with your
   manager.
6. Tell me about a time when you had to fire someone.
7. Tell me about a time when you had to give someone difficult
   feedback.
8. Tell me about a time when you had to deliver hard feedback
   to a direct report.
9. Tell me about a time you had to lead during a crisis.
10. Tell me about a time when you had to deliver difficult
    feedback.
11. Tell me about a time when you had a disagreement with your
    manager.
12. Tell me about a time you had to influence someone without
    authority.
13. Tell me about a time you delegated something important to
    someone on your team.
14. Tell me about a time when you helped an employee grow
    their career.
15. Tell me about a time you mentored someone.
16. Tell me about a time when you had to develop people.
17. Tell me about a time when you had to set goals for your
    team.
18. Tell me about a time when you had to evaluate someone's
    performance.
19. Tell me about a time when you had to make a hiring
    decision.
20. Tell me about a time when you had to retain someone.
21. Tell me about a time when you had to motivate a team.
22. Tell me about a time when you had to manage changing
    priorities.

Your bank should cover at least 15 of the 22. The gaps are
where you'd say "I haven't experienced that directly, but
here's a related situation..." in the interview. The senior
move is to have an answer for everything; the gaps get
smaller with each interview.

---

## Where to go next

- For EM system design framing: see
  `data-engineering-course/system_design/`.
- For behavioral interview foundations: see
  `data-engineering-course/behavioral_interviews/`.
- For getting the interview in the first place: see
  `data-engineering-course/how_to_get_the_interview/`.
- Author articles: <https://medium.com/@premvishnoi>
