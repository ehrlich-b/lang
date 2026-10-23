import json, re, sys
source = sys.argv[1]
# Tokenize separately from the Lang fixture. Offsets remain UTF-8 byte offsets.
lex = re.compile(r'(?P<space>[ \t\r\n]+)|(?P<line>//[^\n]*)|(?P<block>/\*.*?\*/)|(?P<token>-?[0-9]+|[A-Za-z_][A-Za-z_0-9]*|"[A-Za-z_]+"|.)', re.S)
tokens=[]
for m in lex.finditer(source):
    if m.lastgroup == 'token': tokens.append((m.group(),len(source[:m.start()].encode()),len(source[:m.end()].encode())))
text=' '.join(x[0] for x in tokens)
valid=re.fullmatch('chain -?\\d+',text) is not None
if not valid:
    print(json.dumps({"ok":False})); sys.exit(0)
nums=[int(w) for w,_,_ in tokens if re.fullmatch(r'-?[0-9]+',w)]
words=[w for w,_,_ in tokens[1:] if (re.fullmatch(r'[A-Za-z_]\w*',w) or w.startswith('"'))]
value=sum(nums)
start=tokens[0][1]; end=tokens[-1][2]
print(json.dumps({"ok":True,"value":value,"start":start,"end":end}))
