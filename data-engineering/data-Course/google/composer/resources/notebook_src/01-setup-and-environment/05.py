import pipeline_logic
import templating

print("pipeline_logic ->", pipeline_logic.__file__)
print("templating     ->", templating.__file__)
print()
print("pipeline_logic exports:")
for name in sorted(n for n in dir(pipeline_logic) if not n.startswith("_")):
    obj = getattr(pipeline_logic, name)
    if callable(obj):
        print(f"  {name}()")
