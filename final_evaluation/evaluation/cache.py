import json,sqlite3,time,hashlib
from afe.cache import Cache as BaseCache
from afe.policy import FORMATS
from reused.core import digest,read_json,parse
from .common import ROOT,DIAGNOSTIC,config,load,verify_freeze

class Cache(BaseCache):
    def __init__(self,path,cfg=None):super().__init__(path,cfg or config())
    def fill_final(self,questions,model,freeze_path):
        frozen=verify_freeze(freeze_path)
        if digest(questions)!=frozen['final_manifest_hash']:raise ValueError('Final question manifest changed or wrong pool')
        if self.config!=frozen['configuration']:raise ValueError('Final cache configuration differs from freeze')
        for index,q in enumerate(questions):
            for f in range(5):
                key,msg,mapping,identity=self.request(q,f);old=self.store.get(key)
                if old is not None:
                    if old['split']!='final' or old['request_identity']!=identity:raise ValueError('Final cache isolation violation')
                    continue
                attempt=self.store.begin('generation','final',1)
                try:
                    output=model.generate([msg],False,0)[0]
                    result={**output,**parse(output['raw'],mapping),'qid':q['id'],'format_index':f,'format':FORMATS[f],'split':'final',
                      'request_identity':identity,'key':key,'mapping':mapping,'created_unix':time.time(),'parse_status':'valid' if parse(output['raw'],mapping)['valid'] else 'invalid_letter',
                      'raw_sha256':hashlib.sha256(output['raw'].encode()).hexdigest(),'max_new_tokens':self.config['model']['target_max_tokens']}
                    self.store.put(key,'response','final',result);self.store.finish(attempt)
                    if (index*5+f+1)%20==0:print(f'final cache complete={index*5+f+1}/{len(questions)*5}',flush=True)
                except BaseException as error:self.store.finish(attempt,'failed',{'error':repr(error)});raise
    def row(self,q,f,split):
        key,*_=self.request(q,f);r=self.store.get(key)
        if r is None:raise ValueError('Incomplete matrix '+q['id']+'/'+str(f))
        if r['split']!=split or digest(r['request_identity'])!=key:raise ValueError('Cache identity/split mismatch')
        return r
    def import_development(self,questions,split='development'):
        source=DIAGNOSTIC/'runs/main/responses.sqlite';db=sqlite3.connect(f'file:{source}?mode=ro',uri=True);rows=[]
        try:
            for q in questions:
                if q['id'] in {r['id'] for r in load('final')}:raise ValueError('Final ID entered development import')
                for f in range(5):
                    key,*_=self.request(q,f)
                    if self.store.get(key) is not None:continue
                    item=db.execute("select payload from records where key=? and kind='response'",(key,)).fetchone()
                    if item is None:raise ValueError('Incompatible development cache')
                    r=json.loads(item[0]);assert digest(r['request_identity'])==key
                    rows.append((key,'response',split,{**r,'split':split,'reused_source':str(source)}))
            self.store.many(rows)
        finally:db.close()
        return len(rows)
