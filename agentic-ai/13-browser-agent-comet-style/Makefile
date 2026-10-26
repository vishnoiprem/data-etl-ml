.PHONY: test smoke

test:
\tnode -e "const p = require('./extension/privacy.js'); const cases = ['https://chase.com/login', 'https://news.ycombinator.com', 'https://mail.google.com', 'https://stackoverflow.com/questions']; for (const c of cases) console.log(c, p.isUrlBlocked(c));"

smoke:
\tmake test
