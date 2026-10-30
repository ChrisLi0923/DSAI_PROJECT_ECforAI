"""Pure transformations and metrics. A semantic identity is an original option index."""
from __future__ import annotations
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

SEEN = ('original', 'inline', 'bullets', 'rotate1', 'rotate2')
WITHHELD = ('table', 'choices_first', 'reverse')
REPEAT = 'repeat'
MANUAL = 'Solve the science multiple-choice question carefully. Choose the single best answer based on its content, regardless of layout or option order.'
CONTRACT = 'Return exactly one uppercase displayed option letter (A, B, C, or D). Do not add any other text.'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text())

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.flush()
        import os
        os.fsync(f.fileno())
    temp.replace(path)

def normalize(text):
    return re.sub(r'\s+', ' ', text).strip().casefold()

def screen(row):
    texts = row['choices']['text']
    labels = row['choices']['label']
    reasons = []
    if len(texts) != 4 or len(labels) != 4 or len(set(labels)) != 4:
        reasons.append('requires_four_distinct_labels')
    if len(set(map(normalize, texts))) != len(texts):
        reasons.append('duplicate_options')
    if any(not normalize(t) for t in texts) or not normalize(row['question']):
        reasons.append('empty_text')
    if row['answerKey'] not in labels:
        reasons.append('missing_gold')
    joined = ' '.join([row['question']] + texts)
    # Conservative text-only subset. False positives are preferable to broken variants.
    if re.search(r'\b(diagram|figure|illustration|pictured|picture|graph|table|image|map)\b|<img|\[image\]', joined, re.I):
        reasons.append('possible_missing_media')
    if re.search(r'\b(all|none|both|either|neither)\b.{0,25}\b(above|below|[A-D](?:\s+and\s+[A-D])?)\b|\b(option|choice|answer)\s*[A-D1-4]\b|\b[A-D]\s+(?:and|or)\s+[A-D]\b|\b(first|second|third|fourth|last|previous)\s+(?:option|choice|answer)\b', joined, re.I):
        reasons.append('option_position_reference')
    return sorted(set(reasons))

def canonicalize(row, source):
    return {'id': row['id'], 'source': source, 'question': row['question'],
            'options': row['choices']['text'], 'source_labels': row['choices']['label'],
            'gold': row['choices']['label'].index(row['answerKey'])}

def question_key(q):
    # Detect exact normalized content duplicates even when IDs/option order differ.
    return digest([normalize(q['question']), sorted(map(normalize, q['options']))])

def render(q, template):
    if template not in (*SEEN, *WITHHELD, REPEAT):
        raise ValueError(template)
    order = list(range(4))
    if template.startswith('rotate'):
        k = int(template[-1])
        order = order[k:] + order[:k]
    if template == 'reverse':
        order = order[::-1]
    pairs = [(chr(65 + i), q['options'][identity]) for i, identity in enumerate(order)]
    lines = '\n'.join(f'{letter}. {text}' for letter, text in pairs)
    if template == 'inline':
        text = q['question'] + '\n' + '  '.join(f'({a}) {t}' for a, t in pairs)
    elif template == 'bullets':
        text = q['question'] + '\n' + '\n'.join(f'- {a}: {t}' for a, t in pairs)
    elif template == 'table':
        text = q['question'] + '\nLetter | Choice\n--- | ---\n' + '\n'.join(f'{a} | {t}' for a, t in pairs)
    elif template == 'choices_first':
        text = 'Choices:\n' + lines + '\nQuestion: ' + q['question']
    else:
        text = q['question'] + '\n' + lines
    return text, dict(zip('ABCD', order))

def parse(raw, mapping):
    stripped = raw.strip()
    valid = re.fullmatch(r'[A-D]', stripped) is not None
    return {'raw': raw, 'letter': stripped if valid else None,
            'identity': mapping[stripped] if valid else None, 'valid': valid}

def metric_vector(records, templates=SEEN):
    groups = defaultdict(dict)
    for r in records:
        if r['template'] in templates:
            if r['template'] in groups[r['qid']]:
                raise ValueError('duplicate prediction')
            groups[r['qid']][r['template']] = r
    if not groups or any(set(g) != set(templates) for g in groups.values()):
        raise ValueError('incomplete question groups')
    out = {}
    for qid, group in sorted(groups.items()):
        correct = [int(group[t]['correct']) for t in templates]
        out[qid] = {'accuracy': sum(correct)/len(correct), 'robust': int(all(correct)),
                    'invalid': sum(not group[t]['valid'] for t in templates)/len(templates)}
        if 'original' in templates:
            out[qid]['original'] = int(group['original']['correct'])
    return out

def fitness(records, objective):
    v = metric_vector(records, ('original',) if objective == 'original' else SEEN)
    key = {'original': 'original', 'average': 'accuracy', 'robust': 'robust'}[objective]
    return sum(r[key] for r in v.values()) / len(v)

def diagnostics(records, thresholds):
    vectors = metric_vector(records)
    n = len(vectors)
    originals = {r['qid']: r for r in records if r['template'] == 'original'}
    repeats = {r['qid']: r for r in records if r['template'] == REPEAT}
    if set(originals) != set(repeats):
        raise ValueError('missing repeat controls')
    valid_pairs = [(r, repeats[q]) for q, r in originals.items() if r['valid'] and repeats[q]['valid']]
    disagreement = sum(a['identity'] != b['identity'] for a, b in valid_pairs)
    raw_disagreement = sum(r['raw'] != repeats[q]['raw'] for q, r in originals.items())
    any_flip = 0
    eligible_groups = 0
    for qid, original in originals.items():
        other = [r for r in records if r['qid'] == qid and r['template'] in SEEN[1:] and r['valid']]
        if original['valid'] and other:
            eligible_groups += 1
            any_flip += any(r['identity'] != original['identity'] for r in other)
    invalid = sum(not r['valid'] for r in records) / len(records)
    robust = sum(x['robust'] for x in vectors.values()) / n
    sensitivity = any_flip / eligible_groups if eligible_groups else 0
    repeat_rate = disagreement/len(valid_pairs) if valid_pairs else 1
    reasons = []
    if invalid > thresholds['max_invalid_rate']: reasons.append('malformed_output_rate')
    if repeat_rate > thresholds['max_repeat_disagreement']: reasons.append('identical_input_instability')
    if raw_disagreement/n > thresholds['max_repeat_disagreement']: reasons.append('identical_raw_response_instability')
    if sensitivity < thresholds['min_semantic_flip_group_rate']: reasons.append('negligible_format_sensitivity')
    if robust <= thresholds['min_robust_rate']: reasons.append('robust_score_near_zero')
    return {'passed': not reasons, 'stop_reasons': reasons, 'questions': n, 'invalid_rate': invalid,
            'robust_rate': robust, 'semantic_flip_group_rate': sensitivity,
            'semantic_flip_group_denominator': eligible_groups,
            'repeat_disagreement_rate': repeat_rate, 'repeat_valid_pairs': len(valid_pairs),
            'repeat_raw_disagreement_rate': raw_disagreement/n, 'thresholds': thresholds}

def candidate_limit(budget, groups, objective):
    cost = groups * (1 if objective == 'original' else len(SEEN))
    if budget % cost:
        raise ValueError('budget must divide into full, uniform candidate evaluations')
    return budget // cost
