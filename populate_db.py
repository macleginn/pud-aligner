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


db_connect = create_engine('sqlite:///pud.db')

# Source language data
with open('en_pud-ud-test.conllu', 'r') as inp:
    en_chunks = inp.read().strip().split('\n\n')

# Target language data
with open('ru_pud-ud-test.conllu', 'r') as inp:
    ru_chunks = inp.read().strip().split('\n\n')

assert(len(en_chunks) == len(ru_chunks))

en_dict = {}
ru_dict = {}

fill_dict(en_chunks, en_dict)
fill_dict(ru_chunks, ru_dict)

for key in en_dict:
    if key not in ru_dict:
        raise ValueError('Non-aligned sentence ids')

with db_connect.connect() as conn:
    meta = MetaData()
    meta.reflect(bind=db_connect)   
    pud_table = Table('en-ru', meta, autoload=True)
    for key in en_dict:
        stmt = pud_table.insert().values(
            document_id = key[0],
            sentence_id = key[1],
            en = en_dict[key],
            ru = ru_dict[key],
            alignment = '',
            verified = 0
            )
        conn.execute(stmt)
