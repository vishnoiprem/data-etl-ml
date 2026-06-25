import copy
from typing import Any


def migrate_records(records: list[dict], operations: list[dict]) -> list[dict]:

    def get_nested(record: dict, keys: list[str]) -> tuple[Any, bool]:
        current = record
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None, False
            current = current[key]
        return current, True

    def set_nested(record: dict, keys: list[str], value: Any) -> None:
        current = record
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def del_nested(record: dict, keys: list[str]) -> None:
        current = record
        for key in keys[:-1]:
            if not isinstance(current, dict) or key not in current:
                return
            current = current[key]
        current.pop(keys[-1], None)

    def apply_op(record: dict, op: dict) -> None:
        keys = op["path"].split(".")

        match op["op"]:
            case "rename":
                value, found = get_nested(record, keys)
                if not found:
                    return
                del_nested(record, keys)
                set_nested(record, keys[:-1] + [op["new_name"]], value)

            case "cast":
                value, found = get_nested(record, keys)
                if not found:
                    return
                caster = {"int": int, "float": float, "str": str}[op["target_type"]]
                set_nested(record, keys, caster(value))

            case "remove":
                del_nested(record, keys)

            case "add":
                set_nested(record, keys, op["default"])

    result = []
    for record in records:
        r = copy.deepcopy(record)
        for op in operations:
            apply_op(r, op)
        result.append(r)

    return result


# ── Tests ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Test 1: base case from problem
    records = [{"age": "30", "tmp": "x", "addr": {"zip": "10001"}, "name": "Alice"}]
    ops = [
        {"op": "rename", "path": "name",         "new_name": "full_name"},
        {"op": "cast",   "path": "age",           "target_type": "int"},
        {"op": "remove", "path": "tmp"},
        {"op": "add",    "path": "addr.country",  "default": "US"},
    ]
    result = migrate_records(records, ops)
    assert result == [{"age": 30, "addr": {"zip": "10001", "country": "US"}, "full_name": "Alice"}]
    print("✅ Test 1 passed:", result)

    # Test 2: missing path is a no-op (rename / remove / cast)
    records2 = [{"x": 1}]
    ops2 = [
        {"op": "rename", "path": "missing",  "new_name": "nope"},
        {"op": "cast",   "path": "missing",  "target_type": "int"},
        {"op": "remove", "path": "missing"},
    ]
    result2 = migrate_records(records2, ops2)
    assert result2 == [{"x": 1}]
    print("✅ Test 2 passed:", result2)

    # Test 3: add creates intermediate dicts
    records3 = [{}]
    ops3 = [{"op": "add", "path": "a.b.c", "default": 99}]
    result3 = migrate_records(records3, ops3)
    assert result3 == [{"a": {"b": {"c": 99}}}]
    print("✅ Test 3 passed:", result3)

    # Test 4: cast float and str
    records4 = [{"price": "9.99", "code": 42}]
    ops4 = [
        {"op": "cast", "path": "price", "target_type": "float"},
        {"op": "cast", "path": "code",  "target_type": "str"},
    ]
    result4 = migrate_records(records4, ops4)
    assert result4 == [{"price": 9.99, "code": "42"}]
    print("✅ Test 4 passed:", result4)

    # Test 5: multiple records, original not mutated
    original = [{"name": "Bob", "age": "25"}, {"name": "Eve", "age": "30"}]
    ops5 = [
        {"op": "rename", "path": "name", "new_name": "full_name"},
        {"op": "cast",   "path": "age",  "target_type": "int"},
    ]
    result5 = migrate_records(original, ops5)
    assert result5 == [{"full_name": "Bob", "age": 25}, {"full_name": "Eve", "age": 30}]
    assert original[0]["name"] == "Bob"     # original untouched
    print("✅ Test 5 passed:", result5)

    # Test 6: nested rename
    records6 = [{"addr": {"city": "NYC"}}]
    ops6 = [{"op": "rename", "path": "addr.city", "new_name": "town"}]
    result6 = migrate_records(records6, ops6)
    assert result6 == [{"addr": {"town": "NYC"}}]
    print("✅ Test 6 passed:", result6)

    print("\n🎉 All tests passed!")