import re, sys;
print(
    '\n'.join(
        [re.sub(r'(?<![ \d])\d+', '', line) 
            for line in sys.stdin
            ]), end=''
)