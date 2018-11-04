from sqlalchemy import create_engine, Table, MetaData, select, insert


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

        
def fill_alignment_dict(chunks, alignment_lines, alignment_dict):
    """Assumes that alignments go in the same order as the chunks
    in the source-language corpus."""
    cur_doc_id = ''    
    for i,c in enumerate(chunks):
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
        alignment_dict[(cur_doc_id, sent_id)] = alignment_lines[i]


db_connect = create_engine('sqlite:///pud.db')

# Source language data
with open('en_pud-ud-test.conllu', 'r') as inp:
    en_chunks = inp.read().strip().split('\n\n')

# Target language data
with open('ru_pud-ud-test.conllu', 'r') as inp:
    ru_chunks = inp.read().strip().split('\n\n')

# Alignment data
with open('en-ru.align', 'r') as inp:
    alignment_lines = inp.read().strip().splitlines()

assert(len(en_chunks) == len(ru_chunks) == len(alignment_lines))

en_dict = {}
ru_dict = {}
alignment_dict = {}

fill_dict(en_chunks, en_dict)
fill_dict(ru_chunks, ru_dict)
fill_alignment_dict(en_chunks, alignment_lines, alignment_dict)

for key in en_dict:
    if key not in ru_dict:
        raise ValueError('Non-aligned sentence ids')
    
with db_connect.connect() as conn:
    meta = MetaData()
    meta.reflect(bind=db_connect)   
    pud_table = Table('en-ru', meta, autoload=True)
    conn.execute(pud_table.delete())
    for key in en_dict:
        stmt = pud_table.insert().values(
            document_id = key[0],
            sentence_id = key[1],
            en = en_dict[key],
            ru = ru_dict[key],
            alignment = alignment_dict[key],
            verified = 0
            )
        conn.execute(stmt)
