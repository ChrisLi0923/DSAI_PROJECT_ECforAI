"""Fixed BM25. This module has no annotations, labels, prediction or cache imports."""
import collections,hashlib,re,unicodedata
import numpy as np

def normalize_fact(text):
    text=unicodedata.normalize('NFKC',text).strip()
    if len(text)>=2 and text[0]==text[-1]=='"':text=text[1:-1].strip()
    text=re.sub(r'\s+',' ',text).casefold()
    return text[:-1].rstrip() if text.endswith('.') else text

def tokens(text):return re.findall(r"\b\w+(?:['’]\w+)*\b",unicodedata.normalize('NFKC',text).casefold())

def query(stem,options):
    # Narrow argument surface deliberately makes labels, IDs and gold facts unavailable.
    return stem+'\n'+'\n'.join(sorted(options,key=lambda x:(normalize_fact(x),x)))

def documents(lines):
    unique={};duplicates=[]
    for i,line in enumerate(lines):
        text=unicodedata.normalize('NFKC',line).strip()
        if not text:continue
        if len(text)>=2 and text[0]==text[-1]=='"':text=text[1:-1].strip()
        text=re.sub(r'\s+',' ',text);key=normalize_fact(text)
        docid='obqa-fact-'+hashlib.sha256(key.encode()).hexdigest()[:20]
        if key in unique:duplicates.append({'line':i+1,'duplicate_of':unique[key]['source_line']});continue
        unique[key]={'id':docid,'text':text,'normalized':key,'source_line':i+1}
    docs=sorted(unique.values(),key=lambda x:x['id'])
    if len({d['id'] for d in docs})!=len(docs):raise ValueError('stable document-ID collision')
    return docs,duplicates

class BM25:
    def __init__(self,docs,k1=1.5,b=.75):
        self.docs=sorted(docs,key=lambda x:x['id']);self.k1=k1;self.b=b;self.n=len(docs)
        if self.n<3:raise ValueError('Require at least three corpus documents')
        bags=[collections.Counter(tokens(d['text'])) for d in self.docs]
        self.length=np.array([sum(x.values()) for x in bags],float);self.avg=float(self.length.mean())
        self.postings={}
        for i,bag in enumerate(bags):
            for term,count in bag.items():self.postings.setdefault(term,[]).append((i,count))
    def scores(self,text):
        out=np.zeros(self.n);bag=collections.Counter(tokens(text))
        for term,qtf in sorted(bag.items()):
            posting=self.postings.get(term)
            if not posting:continue
            idx=np.array([p[0] for p in posting]);tf=np.array([p[1] for p in posting],float);df=len(idx)
            idf=np.log1p((self.n-df+.5)/(df+.5))
            out[idx]+=qtf*idf*(tf*(self.k1+1))/(tf+self.k1*(1-self.b+self.b*self.length[idx]/self.avg))
        return out
    def rank(self,stem,options):
        text=query(stem,options);scores=self.scores(text)
        # Stable docs already sorted by ID; stable score sort retains deterministic ties.
        order=np.argsort(-scores,kind='stable')[:3]
        return text,[{'id':self.docs[i]['id'],'text':self.docs[i]['text'],'score':float(scores[i])} for i in order]
