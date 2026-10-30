import sqlite3,json
from pathlib import Path
from afe.cache import Cache as OriginalCache
from reused.core import digest,read_json

class Cache(OriginalCache):
    def import_split(self,questions,split,source,source_split=None):
        source_split=source_split or split;db=sqlite3.connect(f'file:{source}?mode=ro',uri=True);rows=[]
        for q in questions:
            for f in range(5):
                key,*_=self.request(q,f)
                if self.store.get(key) is not None:continue
                row=db.execute('SELECT payload FROM records WHERE key=? AND kind=?',(key,'response')).fetchone()
                if row is None:raise ValueError('Incompatible/missing source response '+q['id'])
                value=json.loads(row[0])
                if value['split']!=source_split or digest(value['request_identity'])!=key:raise ValueError('Source split/key mismatch')
                value={**value,'split':split,'reused_source_cache':str(source)}
                rows.append((key,'response',split,value))
        self.store.many(rows);db.close();return len(rows)
    def fill(self,questions,split,model):
        if split=='test':
            path=Path(self.store.path).parent/'FROZEN.json'
            if not path.exists():raise ValueError('test inference before freeze')
            frozen=read_json(path)
            if digest({k:v for k,v in frozen.items() if k!='sha256'})!=frozen['sha256']:raise ValueError('invalid policy freeze')
            if digest(questions)!=frozen['test_manifest_hash']:raise ValueError('test pool differs from freeze')
        return super().fill(questions,split,model)
    def costs(self):
        result=super().costs()
        for split,metric in result['cache_generation'].items():
            rows=self.store.all('response',split);metric['executed_here_calls']=sum('reused_source_cache' not in r for r in rows)
            metric['reused_previous_calls']=sum('reused_source_cache' in r for r in rows)
            metric.pop('reused_preflight_calls',None)
            if metric['reused_previous_calls']:metric['note']='Generation tokens/time are historical source costs, not newly executed follow-up inference.'
        return result
