"""Structured Markdown, editable DOCX and paginated PDF with embedded figures/tables."""
import html,re,os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
pdfmetrics.registerFont(TTFont('ProjectSans',FONT));pdfmetrics.registerFont(TTFont('ProjectSansBold',FONT.replace('.ttf','-Bold.ttf')))
pdfmetrics.registerFontFamily('ProjectSans',normal='ProjectSans',bold='ProjectSansBold',italic='ProjectSans',boldItalic='ProjectSansBold')

def inline(text):
    value=html.escape(str(text));value=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',value)
    value=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#285a88">\1</link>',value)
    return value

def polish(text):
    # Editorial spacing only; opaque hashes, model names, policy IDs and file paths stay intact.
    text=str(text).replace('15November2026','15 November 2026').replace('30October2026','30 October 2026')
    words='Study|Table|Figure|ICLR|ICML|PMLR|EMNLP|NAACL|ACL|COLM|Nature|arXiv|preprint|pilot|search|validation|final|training|reserved|the|a|all|on|at|from|with|versus|than|accuracy|mutation|guidance|seed|seeds|Deadline'
    text=re.sub(r'\b('+words+r')(?=\d)',r'\1 ',text)
    text=re.sub(r'(?<=\d)(?=(?:questions|calls|tokens|minutes|seconds|replicates|points|words|files|seeds)\b)',' ',text)
    text=re.sub(r'(?<=[A-Za-z)])(?=\[\d+\])',' ',text)
    return text

def render(blocks,stem,title,one_page=False):
    stem=Path(stem);stem.parent.mkdir(parents=True,exist_ok=True);width,height=A4;margin=45 if not one_page else 36;usable=width-2*margin
    styles=getSampleStyleSheet();base=9.2 if not one_page else 8.3
    styles.add(ParagraphStyle(name='BodyProject',fontName='ProjectSans',fontSize=base,leading=base*1.42,spaceAfter=7))
    styles.add(ParagraphStyle(name='SmallProject',fontName='ProjectSans',fontSize=7.1,leading=10.2,spaceAfter=5))
    styles.add(ParagraphStyle(name='TableProject',fontName='ProjectSans',fontSize=7.1 if not one_page else 7.0,leading=9.4))
    for key,size in [('Title',19 if not one_page else 14),('Heading1',13 if not one_page else 11),('Heading2',11 if not one_page else 9.5),('Heading3',9.8)]:
        styles[key].fontName='ProjectSansBold';styles[key].fontSize=size;styles[key].leading=size*1.28;styles[key].spaceBefore=12 if not one_page else 7;styles[key].spaceAfter=7
    flow=[];md=[];document=Document();section=document.sections[0]
    section.top_margin=Inches(.7);section.bottom_margin=Inches(.7);section.left_margin=Inches(.75);section.right_margin=Inches(.75)
    normal=document.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10.5 if not one_page else 9)
    normal.paragraph_format.space_after=Pt(6)
    footer=section.footer.paragraphs[0];footer.alignment=2
    run=footer.add_run();field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');run._r.addnext(field)
    for block in blocks:
        block=dict(block)
        for key in ('text','caption'):
            if key in block:block[key]=polish(block[key])
        if block['type']=='table':block['headers']=[polish(x) for x in block['headers']];block['rows']=[[polish(x) for x in row] for row in block['rows']]
        kind=block['type']
        if kind=='heading':
            level=block.get('level',1);text=block['text'];md.append('#'*level+' '+text);flow.append(Paragraph(inline(text),styles['Title' if level==1 else 'Heading'+str(min(3,level-1))]));document.add_heading(text,level=0 if level==1 else level-1)
        elif kind=='paragraph':
            text=block['text'];md.append(text);flow.append(Paragraph(inline(text),styles['SmallProject' if block.get('small') else 'BodyProject']));plain=re.sub(r'\*\*(.+?)\*\*',r'\1',text);plain=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'\1 (\2)',plain);document.add_paragraph(plain)
        elif kind=='table':
            headers=block['headers'];rows=block['rows'];caption=block.get('caption','')
            md.append('\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join('---' for _ in headers)+'|']+['|'+'|'.join(str(v).replace('|','/') for v in row)+'|' for row in rows]))
            if caption:md.append(caption);flow.append(Paragraph(inline(caption),styles['SmallProject']))
            weights=block.get('weights',[1]*len(headers));widths=[usable*w/sum(weights) for w in weights]
            cells=[[Paragraph(inline(value),styles['TableProject']) for value in row] for row in [headers]+rows]
            table=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5edf5')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#b8c4ce')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));flow.extend([table,Spacer(1,9)])
            if caption:document.add_paragraph(caption,style='Caption')
            dtable=document.add_table(rows=1,cols=len(headers));dtable.style='Light Shading Accent 1'
            for cell,value in zip(dtable.rows[0].cells,headers):cell.text=str(value)
            property=OxmlElement('w:tblHeader');dtable.rows[0]._tr.get_or_add_trPr().append(property)
            for row in rows:
                for cell,value in zip(dtable.add_row().cells,row):cell.text=str(value)
            for row in dtable.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        for r in p.runs:r.font.size=Pt(8)
        elif kind=='figure':
            path=Path(block['path']);caption=block['caption'];md.append(f'![{caption}]({os.path.relpath(path,stem.parent)})')
            from PIL import Image as PILImage
            with PILImage.open(path) as im:w,h=im.size
            picture=Image(str(path),width=usable,height=min(usable*h/w,300));flow.append(KeepTogether([picture,Paragraph(inline(caption),styles['SmallProject'])]));document.add_picture(str(path),width=Inches(6.4));document.add_paragraph(caption,style='Caption')
        elif kind=='pagebreak':flow.append(PageBreak());document.add_page_break()
    def page(canvas,doc):
        canvas.saveState();canvas.setFont('ProjectSans',7);canvas.setFillColor(colors.HexColor('#56616b'));canvas.drawString(margin,20,'DSAI6707 | Evolutionary computation for LLM question answering');canvas.drawRightString(width-margin,20,str(doc.page));canvas.restoreState()
    pdf=stem.with_suffix('.pdf');SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=margin,leftMargin=margin,topMargin=margin,bottomMargin=36,title=title,author='DSAI6707 individual project').build(flow,onFirstPage=page,onLaterPages=page)
    if one_page:
        document.styles['Title'].font.size=Pt(14)
        document.styles['Heading 1'].font.size=Pt(10.5)
        document.styles['Heading 2'].font.size=Pt(9.5)
    document.save(stem.with_suffix('.docx'));stem.with_suffix('.md').write_text('\n\n'.join(md)+'\n')
    from pypdf import PdfReader
    reader=PdfReader(pdf);texts=[p.extract_text() for p in reader.pages]
    if not texts or any(not text.strip() for text in texts):raise ValueError('Blank PDF page')
    if one_page and len(reader.pages)!=1:raise ValueError('Completed-project summary exceeded one page')
    return {'pdf':str(pdf),'pages':len(reader.pages),'text_characters':sum(map(len,texts)),'docx':str(stem.with_suffix('.docx')),'markdown':str(stem.with_suffix('.md'))}
