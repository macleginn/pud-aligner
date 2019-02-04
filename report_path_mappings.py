import sqlite3

from itertools import combinations as combs
from queue import SimpleQueue
from collections import Counter
from pprint import pprint
from sys import argv

fname = 'pud.db'
conn = sqlite3.connect(fname)
cursor = conn.cursor()

# Graph-processging routines

def conll2graph(record):
    """Converts sentences described using CoNLL-U format 
    (http://universaldependencies.org/format.html) to graphs. 
    Returns a dictionary of nodes (wordforms and POS tags indexed 
    by line numbers) together with a graph of the dependencies encoded 
    as adjacency lists of (node_key, relation_label, direction[up or down]) tuples."""
    graph = {}
    nodes = {}
    for line in record.splitlines():
        if line.startswith('#'):
            continue
        fields = line.strip('\n').split('\t')
        key = fields[0]
        # Ignore compound surface keys for aux, du, etc.
        # Ignore hidden additional nodes for orphan handling
        if '-' in key or '.' in key:
            continue
        wordform = fields[1] 
        pos = fields[3]
        parent = fields[6]
        relation = fields[7]
        nodes[key] = { 'wordform': wordform, 'pos': pos }
        if key not in graph:
            graph[key] = []
        if parent not in graph:
            graph[parent] = []
        graph[key].append((parent, relation, 'up'))
        graph[parent].append((key, relation, 'down'))
    return (nodes, graph)


def strip_directions(path):
    """Returns a directionless path with only PUDtags as labels."""
    return list(map(lambda x: x.split('_')[0], path))


def get_path(node1, node2, graph):
    if node1 == node2:
        return []
    
    # BFS with edge labels for paths
    q = SimpleQueue()
    # Remembers where we came from and the edge label
    sources = {}
    
    q.put(node1)
    visited = set()
    visited.add(node1)
    
    while not q.empty():
        current = q.get()
        for neighbour, relation, direction in graph[current]:
            if neighbour == node2:
                path = [relation+'_'+direction]
                source = current
                while source != node1:
                    prev_node, prev_relation, prev_direction = sources[source]
                    path.append(prev_relation+'_'+prev_direction)
                    source = prev_node
                return list(reversed(path))
            elif neighbour not in visited:
                sources[neighbour] = (current, relation, direction)
                q.put(neighbour)
            visited.add(neighbour)
            
    raise ValueError("UD graph is not connected.")


# More helper routines


def normalise_key(k):
    """Converts 0-based indexing to 1-based indexing."""
    try:
        return str(int(k)+1)
    except ValueError: # An 'X' marking a non-aligned word
        return 'X'


def preprocess_alignment(alignment_str):
    en_degrees = Counter()
    fr_degrees = Counter()
    unaligned_en = []
    unaligned_fr = []
    one_to_many_en = {}
    one_to_many_fr = {}
    alignment_edges = alignment_str.split()
    real_edges = []
    resulting_edges = []
    for edge in alignment_edges:
        en, fr = list(map(normalise_key,edge.split('-')))
        if en == 'X':
            unaligned_fr.append(fr)
        elif fr == 'X':
            unaligned_en.append(en)
        else:
            en_degrees[en] += 1
            fr_degrees[fr] += 1
            real_edges.append((en, fr))
    for edge in real_edges:
        en, fr = edge
        if en_degrees[en] > 1:
            if en not in one_to_many_en:
                one_to_many_en[en] = []
            one_to_many_en[en].append(fr)
        elif fr_degrees[fr] > 1:
            if fr not in one_to_many_fr:
                one_to_many_fr[fr] = []
            one_to_many_fr[fr].append(en)
        else:
            resulting_edges.append(edge)
    return (
        unaligned_en,
        unaligned_fr,
        one_to_many_en,
        one_to_many_fr,
        resulting_edges
    )


def extract_raw_sentences(conll):
    """Extracts target and source sentences from the target record."""
    lines = conll.splitlines()
    for l in lines:
        if l.startswith('# text = '):
            target = l.strip('\n')[len('# text = '):]
            for l2 in lines:
                if l2.startswith('# text_en = '):
                    source = l2.strip('\n')[len('# text_en = '):]
                    return (source, target)
            else:
                raise ValueError('No source sentence found')
    else:
        raise ValueError('No target sentence found')


def get_edge_label_report(corpus, path_str):
    # Iterate over aligned records in the db
    # From each record extract all edges with
    # corresponding edge labels and their
    # counterparts with marked-up examples.
    # Classify by counterparts and return in the
    # of decreasing group sizes.
    result = []
    temp_dict = {}
    for i, record in enumerate(cursor.execute(f'select `en`,`ru`,`alignment` from `{corpus}` where verified = 1')):
        en, ru, alignment = record
        en_n, en_g = conll2graph(en)
        ru_n, ru_g = conll2graph(ru)
        alignment_dict = {}
        (
            unaligned_en,
            _,
            one_to_many_en,
            one_to_many_ru,
            resulting_edges
        ) = preprocess_alignment(alignment)
        for edge in resulting_edges:
            head, tail = edge
            alignment_dict[head] = tail
        for tail, en_node_set in one_to_many_ru.items():
            for head in en_node_set:
                alignment_dict[head] = tail
        accounted_for = set.union(set(alignment_dict), unaligned_en)
        # Ignore one-to-many, but record unaligned and many-to-one
        for pair in combs(en_n, 2):
            en_head, en_tail = pair
            path_en = '->'.join(
                strip_directions(
                    get_path(
                        en_head, en_tail, en_g)))
            if path_en != path_str:
                continue
            elif en_head in one_to_many_en or en_tail in one_to_many_en:
                continue
            elif en_head in unaligned_en and en_tail in unaligned_en:
                key = 'Both endpoints unaligned'
                ru_head = ru_tail = ''
            elif en_head not in accounted_for or en_tail not in accounted_for:
                # Some asemantical stuff like pseudo-amod
                # or possibly an error
                print(
                    'Something is missing from the alignment dict', 
                    i+1, 
                    f'{en_head} ({en_n[en_head]["wordform"]})', 
                    f'{en_tail} ({en_n[en_tail]["wordform"]})'
                )
                print(extract_raw_sentences(ru))
                print(alignment)
                print()
                continue
            elif en_head in unaligned_en:
                key = 'One endpoint unaligned'
                ru_head = ''
                ru_tail = alignment_dict[en_tail]
            elif en_tail in unaligned_en:
                key = 'One endpoint unaligned'
                ru_tail = ''
                ru_head = alignment_dict[en_head]
            else:
                try:
                    ru_head = alignment_dict[en_head]
                    ru_tail = alignment_dict[en_tail]
                except KeyError as e:
                    print(i+1, e)
                    print(extract_raw_sentences(ru))
                    print(alignment)
                    print()
                    continue
                if ru_head == ru_tail:
                    key = 'Nodes collapsed'
                else:
                    key = '->'.join(
                        strip_directions(
                            get_path(
                                ru_head, ru_tail, ru_g)))
            
            # Add the example
            tmp_en = []
            try:
                en_keys = list(map(str, sorted([int(k) for k in en_n])))
            except ValueError as e:
                print(i+1, e)
                print(record)
                print()
                continue
            for k in en_keys:
                if k in {en_head, en_tail}:
                    tmp_en.append(f"<b>{en_n[k]['wordform']}</b>")
                else:
                    tmp_en.append(en_n[k]['wordform'])
            tmp_ru = []
            ru_keys = list(map(str, sorted([int(k) for k in ru_n])))
            for k in ru_keys:
                if k in {ru_head, ru_tail}:
                    tmp_ru.append(f"<b>{ru_n[k]['wordform']}</b>")
                else:
                    tmp_ru.append(ru_n[k]['wordform'])
            
            if key not in temp_dict:
                temp_dict[key] = []
            temp_dict[key].append( f"{' '.join(tmp_en)} -> {' '.join(tmp_ru)}" )
    
    for item in sorted(
        temp_dict.items(),
        key = lambda x: len(x[1]),
        reverse = True
    ):
        result.append(item)
    
    return result

if __name__ == "__main__":
    pprint(get_edge_label_report(argv[1], argv[2]))