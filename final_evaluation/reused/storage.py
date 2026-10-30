"""Durable per-batch records; cached completed rows are never recomputed on resume."""
import json
import sqlite3
import time
from pathlib import Path

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS records (key TEXT PRIMARY KEY, kind TEXT, scope TEXT, payload TEXT);
        CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, kind TEXT, scope TEXT, n INTEGER,
            started REAL, ended REAL, status TEXT, detail TEXT);
        ''')
        self.db.commit()
    def get(self,key):
        r=self.db.execute('SELECT payload FROM records WHERE key=?',(key,)).fetchone()
        return json.loads(r[0]) if r else None
    def put(self,key,kind,scope,payload):
        self.db.execute('INSERT INTO records VALUES (?,?,?,?)',(key,kind,scope,json.dumps(payload)))
        self.db.commit()
    def many(self,rows):
        self.db.executemany('INSERT INTO records VALUES (?,?,?,?)',
                            [(k,kind,s,json.dumps(p)) for k,kind,s,p in rows])
        self.db.commit()
    def all(self,kind,scope=None):
        query='SELECT payload FROM records WHERE kind=?'; params=[kind]
        if scope is not None: query+=' AND scope=?'; params.append(scope)
        return [json.loads(r[0]) for r in self.db.execute(query,params)]
    def count(self,kind,scope):
        return self.db.execute('SELECT count(*) FROM records WHERE kind=? AND scope=?',(kind,scope)).fetchone()[0]
    def begin(self,kind,scope,n):
        cur=self.db.execute('INSERT INTO attempts(kind,scope,n,started,status) VALUES(?,?,?,?,?)',
                            (kind,scope,n,time.time(),'started'))
        self.db.commit(); return cur.lastrowid
    def finish(self,attempt,status='complete',detail=None):
        self.db.execute('UPDATE attempts SET ended=?,status=?,detail=? WHERE id=?',
                        (time.time(),status,json.dumps(detail),attempt)); self.db.commit()
    def recover(self):
        rows=self.db.execute("SELECT id,kind,scope,n FROM attempts WHERE status='started'").fetchall()
        if rows:
            self.db.execute("UPDATE attempts SET status='interrupted_unknown' WHERE status='started'")
            self.db.commit()
        return rows
    def attempts(self):
        self.db.row_factory=sqlite3.Row
        rows=[dict(r) for r in self.db.execute('SELECT * FROM attempts')]
        self.db.row_factory=None
        return rows
