"""Self-contained PDF and editable HTML/RTF without external application state."""
import re,html,textwrap
from pathlib import Path

def write_html(path,text):
    def inline(s):
        s=html.escape(s)
        s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
        s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
        return s
    out=['<!doctype html><html><head><meta charset="utf-8"><style>body{font:11pt serif;max-width:1000px;margin:2em auto;line-height:1.4}table{border-collapse:collapse;font-size:9pt}td,th{border:1px solid #aaa;padding:4px}h1,h2{font-family:sans-serif}a{color:#254e80}</style></head><body>']
    table=False
    for line in text.splitlines():
        if line.startswith('|'):
            if re.fullmatch(r'[| :\-]+',line): continue
            if not table: out.append('<table>');table=True
            out.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in line.strip('|').split('|'))+'</tr>');continue
        if table: out.append('</table>');table=False
        if line.startswith('#'):
            depth=len(line)-len(line.lstrip('#'));out.append(f'<h{depth}>{inline(line.lstrip("# "))}</h{depth}>')
        elif line.strip():out.append('<p>'+inline(line)+'</p>')
    if table:out.append('</table>')
    out.append('</body></html>');path.write_text('\n'.join(out))

def pdf(path,text,title='Project report',one_page=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    # Text PDFs are searchable and include the complete report and bibliography.
    lines=[]
    for raw in text.splitlines():
        raw=raw.replace('**','')
        if raw.startswith('|') and re.fullmatch(r'[| :\-]+',raw):continue
        raw=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',raw)
        lines+=textwrap.wrap(raw,width=110,break_long_words=True,break_on_hyphens=False) or ['']
    per_page=68 if not one_page else max(68,len(lines))
    if one_page and len(lines)>82:raise ValueError('one-page summary too long')
    with PdfPages(path) as pages:
        for offset in range(0,len(lines),per_page):
            fig=plt.figure(figsize=(8.27,11.69));fig.text(.07,.965,title,fontsize=8,color='#555555')
            chunk=lines[offset:offset+per_page]
            for i,line in enumerate(chunk):
                is_heading=line.startswith('#');line=line.lstrip('# ') if is_heading else line
                fig.text(.07,.94-i*.0128,line,fontsize=8.2 if not is_heading else 9.3,fontweight='bold' if is_heading else 'normal',va='top',fontfamily='DejaVu Sans')
            fig.text(.92,.025,str(offset//per_page+1),fontsize=8);pages.savefig(fig);plt.close(fig)
