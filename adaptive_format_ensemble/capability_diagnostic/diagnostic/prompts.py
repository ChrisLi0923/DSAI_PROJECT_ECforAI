"""Outcome-independent prompts and deterministic, label-free parsers."""
import re
from reused.core import MANUAL,CONTRACT,digest,normalize,render,parse

STRATEGIES={
 'principle': MANUAL+'\nFirst briefly state the scientific principle relevant to the question, then choose the best option. Use no more than 40 words before your answer. End with a separate line exactly FINAL: X, replacing X with one uppercase displayed option letter A, B, C, or D. Do not write anything after that line.',
 'elimination': MANUAL+'\nBriefly compare and eliminate the alternatives, then choose the best option. Use no more than 40 words before your answer. End with a separate line exactly FINAL: X, replacing X with one uppercase displayed option letter A, B, C, or D. Do not write anything after that line.',
 'content': MANUAL+'\nSelect the answer by its content first. Return exactly two lines. First write SELECTED_TEXT: followed by the exact complete text of the selected option, without quotation marks. Then write FINAL: X, replacing X with its uppercase displayed option letter A, B, C, or D. Do not write any explanation or other text.'
}
EVIDENCE_WRAPPER='\n\nScience note (consider its relevance when answering):\n{fact}'

def response_parse(raw,mapping,options,mode):
    if mode in ('base','fact','repeat'):
        return {**parse(raw,mapping),'parse_status':'valid' if parse(raw,mapping)['valid'] else 'invalid_letter','text_letter_conflict':False}
    result={'raw':raw,'letter':None,'identity':None,'valid':False,'parse_status':'missing_final','text_letter_conflict':False,'text_identity':None,'letter_identity':None,'text_prefix_letter':None,'text_match_status':None}
    # One explicit final marker at the end, either its own line or sentence suffix.
    # This is a syntax convention; no label or model judge repairs an answer.
    final=re.search(r'(?<!\w)FINAL: ([A-D])\s*$',raw.strip())
    if raw.count('FINAL:')!=1 or final is None:return result
    letter=final.group(1);result.update(letter=letter,letter_identity=mapping[letter])
    if mode=='content':
        lines=raw.strip().splitlines()
        if len(lines)!=2 or not lines[0].startswith('SELECTED_TEXT: '):
            result['parse_status']='invalid_content_structure';return result
        text=lines[0][len('SELECTED_TEXT: '):]
        matches=[i for i,o in enumerate(options) if normalize(o)==normalize(text)]
        result['text_match_status']='exact_normalized'
        # A single conventional displayed-letter prefix is allowed only when the full
        # field did not already match an option. Check its agreement independently.
        prefix=re.fullmatch(r'([A-D])[.)]\s+(.+)',text)
        if not matches and prefix:
            result['text_prefix_letter']=prefix.group(1);result['text_match_status']='single_display_label_prefix_removed'
            matches=[i for i,o in enumerate(options) if normalize(o)==normalize(prefix.group(2))]
        if len(matches)!=1:result['parse_status']='nonunique_or_unmatched_text';return result
        result['text_identity']=matches[0]
        if matches[0]!=mapping[letter] or (result['text_prefix_letter'] is not None and mapping[result['text_prefix_letter']]!=matches[0]):
            result.update(parse_status='text_letter_conflict',text_letter_conflict=True);return result
    result.update(identity=mapping[letter],valid=True,parse_status='valid');return result

def messages(q,kind,fact=None):
    text,mapping=render(q,'original')
    system=STRATEGIES[kind] if kind in STRATEGIES else MANUAL+'\n'+CONTRACT
    if fact is not None:text+=EVIDENCE_WRAPPER.format(fact=fact)
    return [{'role':'system','content':system},{'role':'user','content':text}],mapping

def specification(cfg):
    return {'strategies':STRATEGIES,'evidence_wrapper':EVIDENCE_WRAPPER,'strategy_max_tokens':cfg['strategy_max_tokens'],
            'selection_rule':cfg['strategy_selection'],'parsing':'One FINAL: X marker at end, on its own line or sentence suffix. Content must uniquely match normalized exact option text; one conventional displayed-letter prefix may be removed and is separately recorded and checked for agreement. Any text/prefix/final-letter conflict is invalid. No labels or judge repair outputs.',
            'canonical_ties':'lowest original option index; no valid candidates = -1',
            'oracle_scope':'finite specified response bank only; never a model-wide capability ceiling'}
