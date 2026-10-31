"""Build age bands from the supplied source; never generate clinical targets."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'content'

def blocks(markdown):
    lines=markdown.strip().splitlines();out=[];i=0
    while i<len(lines):
        text=lines[i].strip()
        if not text or text=='---':i+=1;continue
        if text.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
                i+=1
            if rows:out.append(dict(type='table',headers=rows[0],rows=rows[1:]))
            continue
        if text.startswith('#'):
            out.append(dict(type='heading',text=re.sub(r'^#+\s*','',text)));i+=1;continue
        if text.startswith('* '):
            values=[]
            while i<len(lines) and lines[i].strip().startswith('* '):values.append(lines[i].strip()[2:]);i+=1
            out.append(dict(type='list',items=values));continue
        values=[text];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#','|','* ','---')):
            values.append(lines[i].strip());i+=1
        out.append(dict(type='paragraph',text=' '.join(values)))
    return out

def main():
    source=(ROOT/'child_growth_nutrition_source.md').read_text(encoding='utf-8')
    parts=re.split(r'^# (\d+)\.\s+[^\n]+\n',source,flags=re.M)
    sections={int(parts[i]):parts[i+1] for i in range(1,len(parts),2)}
    infant=sections[1];rows=[line for line in infant.splitlines() if line.startswith('|')][2:14]
    bands=[]
    for month,row in enumerate(rows):
        cells=[c.strip() for c in row.strip('|').split('|')]
        if month<6:
            text=infant.split('**Birth to 6 Months**')[1].split('**After Completing 6 Months**')[0]
        else:
            text=infant.split('**After Completing 6 Months**')[1]
        # The 8-month row has a quantity note instead of a meal frequency.
        frequency='2–3 meals daily' if month==8 else cells[2]
        bands.append(dict(id=f'month-{month}',min_months=month,max_months_exclusive=month+1,
            label=cells[0],foods=cells[1],meal_frequency=frequency,blocks=blocks(text)))
    for year in range(1,13):
        section=min(year+1,12)
        bands.append(dict(id=f'year-{year}',min_months=year*12,max_months_exclusive=(year+1)*12,
            label=f'{year}–{year+1} years' if year<12 else '12 years',blocks=blocks(sections[section])))
    content=dict(version='2026-10-31.v1',title='Growth & Nutrition Guide for Children (0–12 Years)',
        provenance='User-supplied educational guide; not an individual diagnosis or prescribed meal plan.',
        age_bands=bands,growth_monitoring=blocks(sections[13]),food_safety=blocks(sections[14]),
        sources=[dict(title='WHO infant and young child feeding',url='https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding'),
            dict(title='ICMR–NIN Dietary Guidelines for Indians 2024',url='https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf'),
            dict(title='WHO Child Growth Standards',url='https://www.who.int/tools/child-growth-standards'),
            dict(title='WHO growth reference 5–19 years',url='https://www.who.int/tools/growth-reference-data-for-5to19-years')],
        notice='General educational guidance. Your clinician adapts it for allergies, feeding difficulties, prematurity or other needs. Growth needs age- and sex-appropriate charts, not adult BMI cutoffs. No supplement dose or individual calorie target is generated.')
    assert len(bands)==24
    (ROOT/'child_growth_nutrition.json').write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Built 24 age bands from supplied source')

if __name__=='__main__':main()
