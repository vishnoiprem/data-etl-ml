import json

SAMPLE_DIR = COURSE_ROOT / "sample_data"
print("sample_data/ contains:")
for path in sorted(SAMPLE_DIR.iterdir()):
    print(f"  {path.name:<26} {path.stat().st_size:>9,} bytes")

print()
print("summary.json:")
print((SAMPLE_DIR / "summary.json").read_text(encoding="utf-8"))
