# 02 — Choosing the Right Language

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

Most candidates pick one of Python, Java, C++, or JavaScript. The right answer is "the one you can write bug-free the fastest", but here's a short guide.

## Python

- Pros: short, expressive, batteries-included (`heapq`, `collections`, `bisect`)
- Cons: 10-100x slower than C++ on tight loops; whitespace is unforgiving in interviews
- Best for: graphs, trees, dynamic programming, anything high-level

## Java

- Pros: standard library is huge; explicit typing catches bugs
- Cons: verbose; `TreeMap` ceremony
- Best for: OOP-heavy questions, system-design-flavored coding

## C++

- Pros: STL is fast, `unordered_map` is a workhorse, deterministic memory
- Cons: pointers, templates, header gymnastics
- Best for: low-level problems, time-critical loops

## JavaScript

- Pros: arrays and objects are ergonomic; `Map`/`Set` are nice
- Cons: equality is treacherous (`==` vs `===`)
- Best for: web-focused roles

## Recommendation

**Pick Python unless your target role is C++/Java-heavy.** This course is in Python.
