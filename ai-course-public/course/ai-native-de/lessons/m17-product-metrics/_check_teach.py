import sys, importlib.util
spec = importlib.util.spec_from_file_location('m17', 'L17-product-metrics.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['m17'] = mod
spec.loader.exec_module(mod)
import _review_100x as r
score = r._teachability_score(mod)
print('teachability_score:', score)
import io
from contextlib import redirect_stdout
buf = io.StringIO()
with redirect_stdout(buf):
    mod.demo()
out = buf.getvalue()
print('len(out):', len(out))
print('lines:', out.count('\n'))
print('out[200:500]:', repr(out[200:500]))
