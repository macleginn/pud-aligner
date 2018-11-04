def fill_dict(chunks, chunk_dict):
    cur_doc_id = ''    
    for c in chunks:
        lines = c.splitlines()
        sent_id = ''
        for l in lines:
            if l.startswith('# newdoc id') or l.startswith('# newdoc_id'):
                cur_doc_id = l.split(' = ')[1]
            elif l.startswith('# sent_id'):
                sent_id = l.split(' = ')[1]
                break
        if not cur_doc_id and sent_id:
            print(c)
            break
        chunk_dict[(cur_doc_id, sent_id)] = c

def extract_tokens(chunk):
    lines = chunk.splitlines()
    lines = [l for l in lines if not l.startswith('#')]
    return [line.split('\t')[1] for line in lines]

# Source language data
with open('en_pud-ud-test.conllu', 'r') as inp:
    en_chunks = inp.read().strip().split('\n\n')

# Target language data
with open('fr_pud-ud-test.conllu', 'r') as inp:
    tg_chunks = inp.read().strip().split('\n\n')

assert(len(en_chunks) == len(tg_chunks))

en_dict = {}
tg_dict = {}

fill_dict(en_chunks, en_dict)
fill_dict(tg_chunks, tg_dict)

for key in en_dict:
    if key not in tg_dict:
        raise ValueError('Non-aligned sentence ids')

ks = sorted(en_dict.keys())

with open('en-fr.align', 'w') as out:
    for k in ks:
        en_toks = ' '.join(extract_tokens(en_dict[k])).lower()
        tg_toks = ' '.join(extract_tokens(tg_dict[k])).lower()
        print(f"{en_toks} ||| {tg_toks}", file = out)
