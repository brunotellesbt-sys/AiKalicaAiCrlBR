"""Export an unlabeled atlas and a separate geographic route index."""
import argparse,html,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from prepare_world_dex_map import decode


def render(source,output):
    source,output=Path(source),Path(output);output.mkdir(parents=True,exist_ok=True)
    r=json.loads((source/'.journey-world-route-chart').read_text())
    im=decode((source/'src/data/journey_world_map.h').read_text()).convert('RGB')
    im.resize((1344,672),Image.Resampling.NEAREST).save(output/'world-map-current.png')
    im.crop((94,35,212,112)).resize((1416,924),Image.Resampling.NEAREST).save(output/'coastal-passages-detail.png')
    review=Image.new('RGB',(1440,360),'#12202e');draw=ImageDraw.Draw(review)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
    panels=[('1 · Norte de Lilycove',(94,55,119,82)),
            ('2 · Two → Three Island',(161,37,207,56)),
            ('3 · Tanoby → Birth Island',(160,95,201,112))]
    for index,(title,box) in enumerate(panels):
        draw.text((index*480+16,12),title,font=font,fill='white')
        crop=im.crop(box);scale=min(448//crop.width,300//crop.height)
        crop=crop.resize((crop.width*scale,crop.height*scale),Image.Resampling.NEAREST)
        review.paste(crop,(index*480+(480-crop.width)//2,50+(300-crop.height)//2))
    review.save(output/'coastal-passages-review.png')
    # Old review drafts must not leave printed names available as the preview.
    for name in ['world-map-named.png','world-map-named.svg']:(output/name).unlink(missing_ok=True)
    nodes={n['map']:n for n in r['nodes']};definitions={p['map']:p['definition'] for p in r['passages']}
    rows=[]
    for n,node in sorted(nodes.items(),key=lambda v:v[1]['name']):
        if not n.startswith('Journey'):continue
        neighbors=sorted({nodes[e['destination' if e['source']==n else 'source']]['name'] for e in r['routes'] if n in (e['source'],e['destination'])})
        definition=definitions.get(n,'Área de navegação que liga '+', '.join(neighbors)+'.')
        rows.append(dict(name=node['name'],definition=definition,position=node['position'],map=n,neighbors=neighbors))
    data=dict(routes=r['routes'],definitions=rows,labels_printed_on_map=False,passages=r['passages'])
    (output/'world-routes.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    items=''.join('<li><strong>'+html.escape(row['name'])+'</strong><p>'+html.escape(row['definition'])+'</p></li>' for row in rows)
    page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Mapa do mundo e rotas marítimas</title><style>body{margin:0;background:#12202e;color:#eef6ff;font:16px system-ui}main{max-width:1500px;margin:auto;padding:20px}h1{font-size:24px}img{width:100%;image-rendering:pixelated}input{padding:10px;font:inherit;width:min(90%,500px)}ul{padding:0;list-style:none;columns:2;column-gap:30px}li{break-inside:avoid;padding:14px 0;border-bottom:1px solid #39536b}p{line-height:1.5}small{color:#adc3da}@media(max-width:700px){ul{columns:1}}</style><main><h1>Mapa do mundo</h1><img src="world-map-current.png" alt="Contorno do mundo com ligações marítimas em linhas retas, sem nomes sobre o desenho"><p>Linhas azuis mostram as ligações de Surf. Os nomes e as definições ficam na lista abaixo e na seleção do mapa no jogo.</p><h2>Rotas e áreas de navegação</h2><input type="search" id="search" placeholder="Buscar nome ou destino" aria-label="Buscar nome ou destino"><ul>'''+items+'''</ul></main><script>document.querySelector('#search').oninput=e=>{const q=e.target.value.toLocaleLowerCase();document.querySelectorAll('li').forEach(li=>li.hidden=!li.textContent.toLocaleLowerCase().includes(q))}</script></html>'''
    (output/'world-routes.html').write_text(page)
    doc=['# Rotas marítimas do mundo','', 'O desenho do mapa não tem rótulos. Os nomes são consultados na seleção do MAP e nesta lista.','', '| Nome | Definição |','| --- | --- |']
    doc.extend('| '+row['name']+' | '+row['definition']+' |' for row in rows)
    (output.parent.parent/'rotas-maritimas.md').write_text('\n'.join(doc)+'\n')
    print('Unlabeled world atlas;',len(rows),'route definitions;',len(r['routes']),'real links')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.source,a.output)
