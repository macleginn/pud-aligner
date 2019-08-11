import sqlite3
import json

from collections import Counter
from queue import Queue
from itertools import combinations as combs


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
        nodes[key] = {
            'wordform': wordform,
            'pos': pos,
            'relation': relation,
            'parent': parent
        }
        if key not in graph:
            graph[key] = []
        if parent not in graph:
            graph[parent] = []
        graph[key].append((parent, relation, 'up'))
        graph[parent].append((key, relation, 'down'))
    return (nodes, graph)


def get_node_depth(node, graph):
    """A BFS-based implementation."""
    cur_depth = 0
    q = Queue()
    q.put(('0',0))
    visited = set()
    visited.add('0')
    while not q.empty():
        current_node, current_depth = q.get()
        for neighbour, *_ in graph[current_node]:
            if neighbour == node:
                return current_depth+1
            elif neighbour not in visited:
                q.put((neighbour, current_depth+1))
            visited.add(neighbour)
    raise IndexError("Target node unreachable")


def highest_or_none(indices, graph):
    if indices[0] == 'X':
        return None
    min_depth = 1000
    argmin = None
    for i in indices:
        key = str(i)
        depth = get_node_depth(key, graph)
        if depth < min_depth:
            min_depth = depth
            argmin = key
    assert argmin is not None
    return argmin


def get_path(node1, node2, graph):
    if node1 == node2:
        return []
    
    # BFS with edge labels for paths
    q = Queue()
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


def one_to_one(alignments):
    en_degrees = Counter()
    fr_degrees = Counter()
    for tail, heads in alignments.items():
        if tail == 'X' or heads == ['X']:
            continue
        for head in heads:
            en_degrees[tail] += 1
            fr_degrees[head] += 1
    # Iterate again, filter by degree
    result = []
    for tail, heads in alignments.items():
        if tail == 'X' or heads == ['X'] or len(heads) > 1:
            continue
        head = heads[0]
        if en_degrees[tail] == 1 and fr_degrees[head] == 1:
            result.append((tail, head))
    return result


def get_data_for_lang(lang, dbpath='pud_current.db'):
    "Not safe from SQL injection attacks. Do not expose."
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    en = []
    ko = []
    alignments = []
    for en_, ko_, alignment_str in cursor.execute(
        f'SELECT `en`, `ru`, `alignment` FROM `en-{lang}` WHERE `verified` = 1'
    ):
        en.append(en_)
        ko.append(ko_)
        alignments.append(json.loads(alignment_str))
    return (en, ko, alignments)