import importlib.util, sys
spec = importlib.util.spec_from_file_location('L4', 'L4-ann-internals.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['L4'] = mod
spec.loader.exec_module(mod)
import inspect
print("Module file:", mod.__file__)
print("Total functions in module:")
n_total = 0
n_doc = 0
for n, fn in inspect.getmembers(mod, inspect.isfunction):
    if n.startswith('_') or n.startswith('test_'):
        continue
    n_total += 1
    co_filename = getattr(fn.__code__, 'co_filename', '?') if hasattr(fn, '__code__') else '?'
    same_file = co_filename == mod.__file__
    has_doc = bool((fn.__doc__ or '').strip())
    if same_file and has_doc:
        n_doc += 1
    elif same_file:
        print(f'NO DOC: {n}')
print(f'Same file total: {n_total}, with doc: {n_doc}, score: {round(n_doc/max(1,n_total)*10)}')