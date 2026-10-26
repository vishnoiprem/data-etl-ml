import importlib.util, sys, os
spec = importlib.util.spec_from_file_location('L7', 'L7-retrieval-ranking.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['L7'] = mod
spec.loader.exec_module(mod)
import inspect
abs_path = os.path.abspath('L7-retrieval-ranking.py')
n_total, n_doc = 0, 0
for n, fn in inspect.getmembers(mod, inspect.isfunction):
    if n.startswith('_') or n.startswith('test_'):
        continue
    if hasattr(fn, '__code__') and fn.__code__.co_filename != abs_path:
        continue
    n_total += 1
    if (fn.__doc__ or '').strip():
        n_doc += 1
    else:
        print(f'NO DOC: {n}')
print(f'Total: {n_total}, with doc: {n_doc}, score: {round(n_doc/max(1,n_total)*10)}')