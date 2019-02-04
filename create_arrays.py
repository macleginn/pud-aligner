#! /usr/bin/env python3

import sqlite3
import pymorphy2
import json
import pandas

from collections import Counter
from itertools import combinations as combs
from queue import SimpleQueue
from sys import argv
from math import log2
from pprint import pprint
from sys import exit

def normalise_key(k):
    """Converts 0-based indexing to 1-based indexing."""
    return str(int(k)+1)


def strip_directions(path):
    """Returns a directionless path with only PUDtags as labels."""
    return list(map(lambda x: x.split('_')[0], path))


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
        if '-' in key:
            continue
        # lemma would be better, but there are no lemmas in Russian PUD
        # take care of this at a later stage
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


def extract_raw_sentences(record):
    """Extracts target and source sentences from the target record."""
    lines = record[3].splitlines()
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


def preprocess_alignment(alignment_str):
    """Extracts unaligned words and one-to-many alignments.
    returns remaining edges as a list."""
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
        en, fr = edge.split('-')
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


def get_node_depth(node, graph):
    """A BFS-based implementation."""
    cur_depth = 0
    q = SimpleQueue()
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


def get_minimum_depth_node(nodes, graph):
    min_depth = 1000
    arg_min = 'X'
    for n in nodes:
        current_depth = get_node_depth(normalise_key(n), graph)
        if current_depth < min_depth:
            min_depth = current_depth
            arg_min = n
    if arg_min == 'X':
        raise ValueError("Minimum-depth node not found")
    return arg_min


def entropy_for_path(path, input_counter):
    """Assumes that there there are path pairs
    in the counter starting with `path`."""
    counter = Counter()
    for key, val in input_counter.items():
        if key[0] == path:
            counter[key] = val
    total = sum(counter.values())
    entropy = 0
    for el in counter:
        probability = counter[el]/total
        entropy += -1 * log2(probability) * probability
    top_probs = [0 for i in range(3)]
    top_paths = ['' for i in range(3)]
    for i, val in enumerate(counter.most_common(3)):
        top_probs[i] = val[1]/total
        top_paths[i] = val[0][1]
    return (entropy, top_probs, top_paths)

def count_for_path(path, input_counter):
    return sum(1 for el in input_counter.elements() if el[0] == path)


if __name__ == '__main__':
    if len(argv) == 1:
        fname = 'pud.db'
    else:
        fname = argv[1]
    conn = sqlite3.connect(fname)
    cursor = conn.cursor()
    en_ru = [r for r in cursor.execute('select * from `en-ru` where `verified` = 1')]
    print(len(en_ru))
    en_fr = [r for r in cursor.execute('select * from `en-fr` where `verified` = 1')]
    print(len(en_fr))

    # Create French table
    path_counter = Counter()
    all_single_edge_paths = set()
    for i, record in enumerate(en_ru):
        en_n, en_g = conll2graph(record[2])
        fr_n, fr_g = conll2graph(record[3])
        (
            unaligned_en, 
            unaligned_fr, 
            one_to_many_en, 
            one_to_many_fr, 
            alignment_edges
        ) = preprocess_alignment(record[4])
        source_sent, target_sent = extract_raw_sentences(record)

    #     aligned_en = [normalise_key(el[1]) for el in alignment_edges] + [normalise_key(el[0]) for el in one_to_many_fr]
    #     unaligned_en = [normalise_key(el) for el in unaligned_fr]
    #     for aligned_node in aligned_en:
    #         for unaligned_node in unaligned_en:
    #             if int(aligned_node) < int(unaligned_node):
    #                 path = get_path(aligned_node, unaligned_node, fr_g)
    #             else:
    #                 path = get_path(unaligned_node, aligned_node, fr_g)
    #             if '->'.join(path) == 'punct_up':
    #                 print(i+1)
    #                 print(en_n)
    #                 print("Aligned:", aligned_node, en_n[aligned_node])
    #                 print("Unaligned:", unaligned_node, en_n[unaligned_node])
    #                 print(source_sent)
    #                 print(record[4])
    #                 exit(0)
    #             path_counter['->'.join(path)] += 1
    # pprint(path_counter.most_common(30))
    # print()

        # Extract highest-positioned counterparts from one-to-many alignments
        for node_fr, nodes_en in one_to_many_fr.items():
            minimum_depth_node_en = get_minimum_depth_node(nodes_en, en_g)
            alignment_edges.append((minimum_depth_node_en, node_fr))
        for node_en, nodes_fr in one_to_many_en.items():
            minimum_depth_node_fr = get_minimum_depth_node(nodes_fr, fr_g)
            alignment_edges.append((node_en, minimum_depth_node_fr))
        alignment_edges.sort(key = lambda x: int(x[0]))
        
        # Extract paths and count them 
        for c in combs(alignment_edges, 2):
            p, q = c
            en1, fr1 = map(normalise_key, p)
            en2, fr2 = map(normalise_key, q)
            if fr_n[fr1]['pos'] == 'CCONJ' or fr_n[fr2]['pos'] == 'CCONJ':
                continue # CCONJs were not aligned for Russian
            path_en = strip_directions(get_path(en1, en2, en_g))
            path_fr = strip_directions(get_path(fr1, fr2, fr_g))
            # path_en = get_path(en1, en2, en_g)
            # path_fr = get_path(fr1, fr2, fr_g)
            if len(path_en) > 1:
                continue
            if path_en[0] not in all_single_edge_paths:
                all_single_edge_paths.add(path_en[0])
            path_counter[(path_en[0], '->'.join(path_fr))] += 1

    path_stats = {
        'path': [],
        'count': [],
        'entropy': [],
        'prob1': [],
        'prob2': [],
        'prob3': [],
        'path1': [],
        'path2': [],
        'path3': []
    }
    for p in all_single_edge_paths:
        entropy, (prob1, prob2, prob3), (path1, path2, path3) = entropy_for_path(p, path_counter)
        path_stats['path'].append(p)
        path_stats['count'].append(count_for_path(p, path_counter))
        path_stats['entropy'].append(entropy)
        path_stats['prob1'].append(prob1)
        path_stats['prob2'].append(prob2)
        path_stats['prob3'].append(prob3)
        path_stats['path1'].append(path1)
        path_stats['path2'].append(path2)
        path_stats['path3'].append(path3)

    df = pandas.DataFrame(path_stats)
    df.to_csv('en-ru-path-entropies-w-paths-directionless.csv', index=False)




    # print(entropy, prob1, prob2, prob3)
    # path_entropies.sort(key = lambda x: x[1], reverse = True)
    # for el in path_entropies:
    #     print(f'{el[0]}: {el[1]}, {el[2]}')
    # df = pandas.DataFrame({
    #     'entropy': [el[1] for el in path_entropies[:20]],
    #     'count': [el[2] for el in path_entropies[:20]]
    # })
    # print(df.corr(method='spearman'))