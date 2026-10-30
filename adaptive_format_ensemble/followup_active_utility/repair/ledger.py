"""Every complete scored replay is durable and charged, including discarded probes."""
import sqlite3,json,time,base64
import numpy as np
from reused.core import digest
from .replay import execute

class Ledger:
    def __init__(self,path,data,budget,identity):
        if data.split!='search' or not len(data.y):raise ValueError('nonempty search data required')
        self.data=data;self.budget=budget;self.path=path
        self.db=sqlite3.connect(path);self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS evaluations(key TEXT PRIMARY KEY,hash TEXT,role TEXT,payload TEXT,seconds REAL,unix REAL);
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY,key TEXT,status TEXT,started REAL,ended REAL);
        CREATE TABLE IF NOT EXISTS archive(hash TEXT PRIMARY KEY,policy TEXT);
        CREATE TABLE IF NOT EXISTS mutations(step INTEGER PRIMARY KEY,payload TEXT);''')
        self.db.commit();self.db.execute("UPDATE attempts SET status='interrupted_unknown' WHERE status='started'");self.db.commit()
        signature={**identity,'budget':budget,'search_data_hash':digest([data.x.tolist(),data.y.tolist()])}
        old=self.meta('identity')
        if old is not None and old!=signature:raise ValueError('search resume identity/config/data mismatch')
        if old is None:self.set_meta('identity',signature)
    def meta(self,key):
        row=self.db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone();return json.loads(row[0]) if row else None
    def set_meta(self,key,value):
        self.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',(key,json.dumps(value)));self.db.commit()
    @property
    def count(self):return self.db.execute('SELECT count(*) FROM evaluations').fetchone()[0]
    @property
    def remaining(self):return self.budget-self.count
    def score(self,policy,key,role):
        h=digest(policy);old=self.db.execute('SELECT hash,payload FROM evaluations WHERE key=?',(key,)).fetchone()
        if old:
            if old[0]!=h:raise ValueError('resume evaluation key changed policy')
            payload=json.loads(old[1])
        else:
            if self.remaining<=0:raise RuntimeError('policy-evaluation budget exceeded')
            attempt=self.db.execute("INSERT INTO attempts(key,status,started) VALUES(?,'started',?)",(key,time.time())).lastrowid;self.db.commit()
            start=time.perf_counter();r=execute(policy,self.data.x);seconds=time.perf_counter()-start
            correct=int(np.sum(r['answer']==self.data.y));calls=int(r['calls'].sum());n=len(self.data.y)
            payload={'answer':r['answer'].tolist(),'calls':r['calls'].tolist(),'correct':correct,'total_calls':calls,
                     'accuracy':correct/n,'mean_calls':calls/n,'utility_numerator':100*correct-calls,'utility':(100*correct-calls)/(100*n),
                     'visits':{'/'.join(p):base64.b64encode(np.packbits(mask).tobytes()).decode() for p,mask in r['visits'].items()} if role=='base' else {}}
            self.db.execute('INSERT INTO evaluations VALUES(?,?,?,?,?,?)',(key,h,role,json.dumps(payload),seconds,time.time()))
            self.db.execute("UPDATE attempts SET status='complete',ended=? WHERE id=?",(time.time(),attempt));self.db.commit()
        result={**payload,'answer':np.array(payload['answer'],dtype=np.int16),'calls':np.array(payload['calls'],dtype=np.int16)}
        result['visits']={tuple(p.split('/')) if p else ():np.unpackbits(np.frombuffer(base64.b64decode(value),dtype=np.uint8))[:len(self.data.y)].astype(bool) for p,value in payload['visits'].items()}
        return result
    def archive(self,policy):
        self.db.execute('INSERT OR IGNORE INTO archive VALUES(?,?)',(digest(policy),json.dumps(policy)));self.db.commit()
    def candidates(self):return [json.loads(p) for p, in self.db.execute('SELECT policy FROM archive ORDER BY hash')]
    def mutation(self,step,audit):
        self.db.execute('INSERT OR REPLACE INTO mutations VALUES(?,?)',(step,json.dumps(audit)));self.db.commit()
    def accounting(self):
        return {'raw_scored_evaluations':self.count,'question_policy_replays':self.count*len(self.data.y),'policy_evaluation_equivalents':self.count,
                'roles':dict(self.db.execute('SELECT role,count(*) FROM evaluations GROUP BY role')),
                'unique_scored_policies':self.db.execute('SELECT count(DISTINCT hash) FROM evaluations').fetchone()[0],
                'archived_candidates':self.db.execute('SELECT count(*) FROM archive').fetchone()[0],
                'attempt_statuses':dict(self.db.execute('SELECT status,count(*) FROM attempts GROUP BY status')),
                'replay_seconds':self.db.execute('SELECT coalesce(sum(seconds),0) FROM evaluations').fetchone()[0]}
