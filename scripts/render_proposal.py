"""Render the concise proposal as one A4 page, without external document tools."""
from pathlib import Path
import re
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
paragraphs=(root/'docs/proposal.md').read_text().strip().split('\n\n')
fig=plt.figure(figsize=(8.27,11.69))
y=.955
fig.text(.07,y,'Advanced Computational Intelligence | Course proposal',fontsize=9,color='#555555')
y-=.038
for i,paragraph in enumerate(paragraphs[1:]):
    paragraph=re.sub(r'\*\*([^*]+)\*\*',r'\1',paragraph).replace('\n',' ')
    if i==0:
        title,_,subtitle=paragraph.partition(' Advanced Computational')
        lines=textwrap.wrap(title,width=67)
        for line in lines:
            fig.text(.07,y,line,fontsize=13,fontweight='bold',va='top'); y-=.024
        if subtitle:
            for line in textwrap.wrap('Advanced Computational'+subtitle,width=108):
                fig.text(.07,y,line,fontsize=9,color='#555555',va='top'); y-=.016
            y-=.012
    else:
        lines=textwrap.wrap(paragraph,width=105)
        for line in lines:
            fig.text(.07,y,line,fontsize=9.2,va='top'); y-=.016
        y-=.010
if y<.045: raise RuntimeError('Proposal exceeds one page')
fig.text(.07,.035,'Prepared 27 October 2026 | Asia/Shanghai | Results pending',fontsize=8,color='#666666')
fig.savefig(root/'docs/proposal.pdf')
plt.close(fig)
print('Wrote one-page docs/proposal.pdf; lowest body position',round(y,3))
