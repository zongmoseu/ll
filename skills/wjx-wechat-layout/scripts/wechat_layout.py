"""Local manuscript -> classified, editable WeChat HTML. No uploading or publishing."""
import argparse
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

SKILL_DIR = Path(__file__).resolve().parents[1]
THEMES = json.loads((SKILL_DIR/'assets/themes.json').read_text(encoding='utf-8'))
COLUMNS = json.loads((SKILL_DIR/'assets/columns.json').read_text(encoding='utf-8'))
COMPONENTS = json.loads((SKILL_DIR/'assets/components.json').read_text(encoding='utf-8'))

def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def compact(text):
    return re.sub(r'\s+', '', text)

def runs_text(runs):
    return ''.join(str(r.get('text', '')) for r in runs)

def blocks_text(blocks):
    parts=[]
    for b in blocks:
        if b['type']=='group':parts.append(blocks_text(b['blocks']))
        elif b['type'] in ('section_label','end_mark'):continue
        elif b['type']=='table':
            for row in b['rows']:
                for cell in row:parts.append(blocks_text(cell['blocks']))
        elif b['type']=='gallery':
            parts.extend(i.get('caption','') for i in b['images'])
        elif b['type'] in ('image','component'):parts.append(b.get('caption',''))
        else:parts.append(runs_text(b.get('runs',[])))
    return '\n'.join(parts)

def classify(title, text='', source_column=None):
    """Title/topic rules are suggestions; ambiguous cases require agent review."""
    rules=[
      ('导师交流','导师交流预告',r'^导师交流|第.{1,8}期.*导师'),
      ('校友动态','校友成果',r'^校友动态|(?:校友|院友|学长|学姐).*(?:荣获|获奖|入选|入职|出版)'),
      ('校友活动','对话校友',r'对话校友|校友.*(?:论坛|返校|聚会)|(?:院友|校友).*(?:分享|交流|共话)|吴院人|致每一位吴院校友'),
      ('通知公告','活动招募',r'招募|招募令'),
      ('通知公告','招生选拔',r'选拔.*(?:公告|通知|安排)|招生.*(?:公告|通知)'),
      ('通知公告','开放安排',r'书院公告|闭馆|开放时间'),
      ('通知公告','值班通知',r'值班安排'),
      ('通知公告','活动预告',r'直播链接|直播预告|活动预告|即将'),
      ('科创竞赛','论文成果',r'科创速递.*论文|论文.*(?:录用|发表)'),
      ('科创竞赛','竞赛日历',r'竞赛日历'),
      ('科创竞赛','项目答辩',r'SRTP|项目.*(?:答辩|验收)'),
      ('科创竞赛','竞赛成果',r'科创速递|智能汽车竞赛|电子设计竞赛'),
      ('科创竞赛','科创育人',r'科创指导'),
      ('党建思政','理论学习',r'党课|政绩观|党总支.*学习|理论学习'),
      ('党建思政','组织建设',r'党员.*宣誓|入党|党支部.*建设'),
      ('党建思政','红色实践',r'党建|党日|红色|英烈|红迹|长征|联学共建'),
      ('国际交流','行前培训',r'(?:国际交流|访学).*行前|行前培训'),
      ('国际交流','访学纪实',r'剑桥|康桥|亚琛|佐治亚|走向国际'),
      ('人物风采','团队风采',r'风采展示|班主任.*(?:来袭|登场)|管理团队.*成员'),
      ('人物风采','健雄学子',r'^健雄学子'),
      ('人物风采','师者风采',r'三育人风采|师者|师说'),
      ('人物风采','新生故事',r'新生故事|骑行上大学'),
      ('人物风采','人物荣誉',r'^喜报.*(?:教授|年度人物|获评)'),
      ('书院活动','人文讲座',r'人文讲座|高峰体验|讲授信念|精彩演讲'),
      ('书院活动','书院互访',r'书院.*(?:互访|跨学科|联盟|交流)|寻脉川蜀|沧海相逢'),
      ('书院活动','文化活动',r'学生节'),
      ('学院新闻','育人工作',r'院长午餐|集训营|奖学金.*答辩|慰问'),
      ('学院新闻','制度发布',r'手册.*发布')]
    for col,sub,pattern in rules:
        if re.search(pattern,title,re.I):return {'column':col,'subtype':sub,'confidence':'title-rule','reason':pattern}
    aliases={'综合新闻':'学院新闻','科创速递':'科创竞赛','党建动态':'党建思政'}
    src=aliases.get(source_column,source_column)
    if src in COLUMNS:return {'column':src,'subtype':'待细分','confidence':'source-only','reason':'来源栏目仅作线索，需结合正文复核'}
    return {'column':'学院新闻','subtype':'待细分','confidence':'needs-review','reason':'标题不能确定；请结合正文语义分类，当前为临时归类'}

def safe_href(value):
    value=str(value)
    if urlparse(value).scheme.lower() not in ('https','http','mailto','tel'):
        raise ValueError('不支持的链接协议：'+value)
    return value

def inline_markdown(text):
    # Deliberately a small subset; no raw HTML is evaluated.
    result=[];pos=0
    pat=r'\*\*([^*]+)\*\*|\[([^\]]+)\]\((https?://[^\s)]+)\)|\*([^*]+)\*'
    for m in re.finditer(pat,text):
        if m.start()>pos:result.append({'text':text[pos:m.start()]})
        if m[1]:result.append({'text':m[1],'bold':True})
        elif m[2]:result.append({'text':m[2],'href':m[3]})
        else:result.append({'text':m[4],'italic':True})
        pos=m.end()
    if pos<len(text):result.append({'text':text[pos:]})
    return result

def extract_text(path):
    title=path.stem;blocks=[];warnings=[];is_md=path.suffix.lower()=='.md'
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():continue
        line=line.strip()
        h=re.match(r'^(#{1,6})\s+(.+)',line) if is_md else None
        if h and len(h[1])==1 and not blocks:
            title=h[2];continue
        if h:blocks.append({'type':'heading','level':min(len(h[1]),3),'runs':inline_markdown(h[2])});continue
        image=re.fullmatch(r'!\[([^\]]*)\]\((.+)\)',line) if is_md else None
        if image:
            src=image[2]
            if urlparse(src).scheme in ('http','https'):raise ValueError('请先将远程稿件图片下载为本地文件：'+src)
            f=(path.parent/src).resolve()
            if not f.is_file():raise ValueError('稿件图片不存在：'+str(f))
            blocks.append({'type':'image','src':str(f),'alt':image[1]});continue
        typ='paragraph';marker=None
        if is_md and line.startswith('> '):typ='quote';line=line[2:]
        elif is_md:
            match=re.match(r'^(\d+[.)]|[-*+])\s+(.+)',line)
            if match:typ='list_item';marker=match[1];line=match[2]
        if re.match(r'^(图文|文字|图片|摄影|编辑|责编|审核|审校|排版|来源)\s*[|｜：:]',line):typ='credit'
        block={'type':typ,'runs':inline_markdown(line) if is_md else [{'text':line}]}
        if marker:block['marker']=marker
        blocks.append(block)
    return title,blocks,warnings

def extract_docx(path, media_dir):
    from docx import Document
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
    from docx.text.run import Run
    doc=Document(str(path));warnings=[];title=path.stem;blocks=[];media_dir.mkdir(parents=True,exist_ok=True)
    if doc.element.xpath('.//w:ins | .//w:del'):
        raise ValueError('检测到修订，请确认最终稿并接受/拒绝修订后再转换')
    if doc.element.xpath('.//m:oMath | .//m:oMathPara'):
        raise ValueError('检测到Word公式，请先转换为清晰图片或等价文本并核对')
    numroot=doc.part.numbering_part.element if doc.part.numbering_part else None
    counters={}
    def numbering(p):
        pp=p._p.pPr
        props=pp.find(qn('w:numPr')) if pp is not None else None
        if props is None and p.style is not None:
            st=p.style.element.find(qn('w:pPr'));props=st.find(qn('w:numPr')) if st is not None else None
        if props is None:return None
        n=props.find(qn('w:numId'));lvl=props.find(qn('w:ilvl'))
        if n is None:return None
        numid=n.get(qn('w:val'));level=int(lvl.get(qn('w:val'))) if lvl is not None else 0
        if numid=='0':return None
        num=next((x for x in numroot if x.tag==qn('w:num') and x.get(qn('w:numId'))==numid),None)
        if num is None:raise ValueError('Word列表编号定义缺失')
        absid=num.find(qn('w:abstractNumId')).get(qn('w:val'))
        abstract=next(x for x in numroot if x.tag==qn('w:abstractNum') and x.get(qn('w:abstractNumId'))==absid)
        lv=next((x for x in abstract if x.tag==qn('w:lvl') and x.get(qn('w:ilvl'))==str(level)),None)
        if lv is None:raise ValueError('不支持的Word列表级别')
        fmt=lv.find(qn('w:numFmt')).get(qn('w:val'));pattern=lv.find(qn('w:lvlText')).get(qn('w:val'))
        start=lv.find(qn('w:start'));start=int(start.get(qn('w:val'))) if start is not None else 1
        for ov in num.findall(qn('w:lvlOverride')):
            st=ov.find(qn('w:startOverride'))
            if ov.get(qn('w:ilvl'))==str(level) and st is not None:start=int(st.get(qn('w:val')))
        if fmt=='bullet':return ('•',level)
        if fmt not in ('decimal','lowerLetter','upperLetter'):
            raise ValueError('暂不自动转换此Word编号格式：'+fmt+'；请保留可见编号后再转换')
        nums=counters.setdefault(numid,{})
        nums[level]=nums.get(level,start-1)+1
        for k in list(nums):
            if k>level:del nums[k]
        def repl(m):
            v=nums.get(int(m[1])-1,1)
            if fmt=='lowerLetter':return chr(96+v) if v<=26 else str(v)
            if fmt=='upperLetter':return chr(64+v) if v<=26 else str(v)
            return str(v)
        return (re.sub(r'%(\d+)',repl,pattern),level)
    def paragraphs(el):
        p=Paragraph(el,doc);name=p.style.name if p.style else '';heading=re.match(r'(?:Heading|标题)\s*([1-6])',name,re.I)
        typ='heading' if heading else ('caption' if name.lower() in ('caption','题注') else 'paragraph')
        out=[];runs=[]
        def flush():
            nonlocal runs
            if runs and any(r.get('text') for r in runs):
                block={'type':typ,'runs':runs}
                if heading:block['level']=min(int(heading[1])+1,3)
                out.append(block)
            runs=[]
        def read_run(el,href=None):
            run=Run(el,p);attrs={}
            for prop in ('bold','italic','underline'):
                val=getattr(run,prop)
                if val is None and run.style is not None:val=getattr(run.style.font,prop)
                if val is None and p.style is not None:val=getattr(p.style.font,prop)
                if val:attrs[prop]=True
            if href:attrs['href']=safe_href(href)
            for child in el:
                tag=child.tag.rsplit('}',1)[-1]
                if tag=='t':runs.append({'text':child.text or '',**attrs})
                elif tag=='tab':runs.append({'text':'\t',**attrs})
                elif tag in ('br','cr'):runs.append({'text':'\n',**attrs})
                elif tag in ('drawing','pict'):
                    flush();found=False
                    for img in child.iter():
                        rid=img.get(qn('r:embed')) or (img.get(qn('r:id')) if img.tag.endswith('imagedata') else None)
                        if not rid:continue
                        part=doc.part.related_parts.get(rid)
                        if part is None:raise ValueError('Word图片关系缺失：'+rid)
                        ext=Path(str(part.partname)).suffix.lower()
                        if ext not in ('.png','.jpg','.jpeg','.gif','.webp','.svg'):
                            raise ValueError('Word图片格式需先转为PNG：'+ext)
                        f=media_dir/(hashlib.sha256(part.blob).hexdigest()[:20]+ext);f.write_bytes(part.blob)
                        out.append({'type':'image','src':str(f.resolve()),'alt':''});found=True
                    if not found:raise ValueError('检测到无法提取的Word图形，请先转为图片后重试')
                elif tag in ('object','sym'):raise ValueError('检测到嵌入对象或特殊符号，请先转换为可见文本或图片')
        for child in el:
            tag=child.tag.rsplit('}',1)[-1]
            if tag=='r':read_run(child)
            elif tag=='hyperlink':
                rid=child.get(qn('r:id'));rel=doc.part.rels.get(rid)
                href=rel.target_ref if rel else None
                for rr in child.findall(qn('w:r')):read_run(rr,href)
            elif tag not in ('pPr','bookmarkStart','bookmarkEnd','proofErr'):
                if list(child.iter(qn('w:t'))):raise ValueError('检测到修订/域/控件内文本，请先接受修订并转换为普通文本，避免遗漏')
        flush();n=numbering(p)
        if n:
            first=next((x for x in out if 'runs' in x),None)
            if first:
                first['type']='list_item';first['marker']=n[0];first['level']=n[1]
        for block in out:
            text=runs_text(block.get('runs',[]))
            if re.match(r'^(图文|文字|图片|摄影|编辑|责编|审核|审校|排版|来源)\s*[|｜：:]',text):block['type']='credit'
        if name.lower() in ('title','标题') and not any(x['type']=='image' for x in out):
            return out,True
        return out,False
    def table(el):
        rows=[];above={}
        for tr in el.findall(qn('w:tr')):
            row=[];column=0;current={}
            for tc in tr.findall(qn('w:tc')):
                pr=tc.find(qn('w:tcPr'));span=pr.find(qn('w:gridSpan')) if pr is not None else None
                span=int(span.get(qn('w:val'))) if span is not None else 1
                merge=pr.find(qn('w:vMerge')) if pr is not None else None
                if merge is not None and merge.get(qn('w:val'),'continue')=='continue':
                    if column not in above:raise ValueError('表格合并关系不完整')
                    origin=above[column];origin['rowspan']=origin.get('rowspan',1)+1
                    for k in range(column,column+span):current[k]=origin
                    column+=span;continue
                contents=[]
                for sub in tc:
                    if sub.tag==qn('w:p'):contents.extend(paragraphs(sub)[0])
                    elif sub.tag==qn('w:tbl'):contents.append(table(sub))
                cell={'blocks':contents,'colspan':span,'rowspan':1};row.append(cell)
                for k in range(column,column+span):current[k]=cell
                column+=span
            above=current;rows.append(row)
        return {'type':'table','rows':rows}
    for child in doc.element.body:
        if child.tag==qn('w:p'):
            chunks,is_title=paragraphs(child)
            if is_title and not blocks and title==path.stem:title=blocks_text(chunks)
            else:blocks.extend(chunks)
        elif child.tag==qn('w:tbl'):blocks.append(table(child))
        elif child.tag!=qn('w:sectPr') and list(child.iter(qn('w:t'))):raise ValueError('检测到不支持的正文容器，请转换为普通段落')
    if doc.element.xpath('.//wp:anchor'):warnings.append('浮动图片按锚点位置插入，需对照Word核对图文顺序。')
    if doc.element.xpath('.//w:txbxContent'):raise ValueError('检测到文本框；请先转换为普通段落，避免文字遗漏')
    if title==path.stem:warnings.append('未检测到Word“标题”样式：请在article.json中确认主标题；未擅自删除首段。')
    if doc.element.xpath('.//w:footnoteReference | .//w:endnoteReference'):
        raise ValueError('检测到脚注或尾注，请先将注释并入正文后转换')
    return title,blocks,warnings

def extract(path, output):
    path=Path(path).resolve();output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    if path.suffix.lower()=='.docx':title,blocks,warnings=extract_docx(path,output.parent/'source-images')
    elif path.suffix.lower() in ('.md','.txt'):title,blocks,warnings=extract_text(path)
    else:raise ValueError('支持 .docx、.md、.txt；旧版 .doc 请先另存为 .docx')
    route=classify(title,blocks_text(blocks))
    inferred_title=any('未检测到Word' in w for w in warnings) if path.suffix.lower()=='.docx' else not (path.suffix.lower()=='.md' and re.match(r'^#\s+',path.read_text(encoding='utf-8-sig').lstrip()))
    article={'version':1,'title':title,'source':str(path),'column':route['column'],'subtype':route['subtype'],'classification':route,'classification_reviewed':False,'blocks':blocks,'warnings':warnings,'source_title_mode':'filename' if inferred_title else 'document','source_filename_title':path.stem}
    article['source_text']=('' if inferred_title else title+'\n')+blocks_text(blocks)
    dump(output,article);return article

def render(article_path, output, theme_name=None, image_map=None, include_title=False):
    from bs4 import BeautifulSoup
    path=Path(article_path).resolve();a=json.loads(path.read_text(encoding='utf-8'));out=Path(output).resolve();out.mkdir(parents=True,exist_ok=True)
    column=a.get('column')
    if column not in COLUMNS:raise ValueError('请先确认栏目；有效栏目：'+', '.join(COLUMNS))
    theme_name=theme_name or a.get('theme') or COLUMNS[column]['theme']
    if theme_name not in THEMES:raise ValueError('未知主题：'+str(theme_name))
    theme={**THEMES[theme_name],**a.get('style_overrides',{})}
    for key in ('primary','light','accent','text'):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',str(theme[key])):raise ValueError('颜色必须为六位十六进制：'+key)
    for key,lo,hi in [('font_size',12,22),('line_height',1.2,2.5),('letter_spacing',0,3)]:
        theme[key]=float(theme[key])
        if not lo<=theme[key]<=hi:raise ValueError('样式参数超出合理范围：'+key)
    inferred_unchanged=a.get('source_title_mode')=='filename' and a['title']==a.get('source_filename_title')
    current=('' if inferred_unchanged else a['title']+'\n')+blocks_text(a['blocks'])
    source_changed=compact(a.get('source_text',current))!=compact(current)
    if source_changed and not a.get('user_authorized_text_changes',False):raise ValueError('内容与提取稿不同：请核对遗漏；只有用户要求改文时才可标记user_authorized_text_changes')
    mapped=json.loads(Path(image_map).read_text(encoding='utf-8')) if image_map else {}
    manifest=[];warnings=list(a.get('warnings',[]));images_dir=out/'images';images_dir.mkdir(exist_ok=True)
    def image(src,role='content',alt='',width=None):
        f=Path(src)
        if not f.is_absolute():f=(path.parent/f).resolve()
        if not f.is_file():raise ValueError('图片不存在：'+str(f))
        if f.suffix.lower() not in ('.png','.jpg','.jpeg','.gif','.webp','.svg'):raise ValueError('不支持的图片格式：'+f.suffix)
        local='images/'+hashlib.sha256(f.read_bytes()).hexdigest()[:20]+f.suffix.lower()
        dest=out/local
        if f.resolve()!=dest.resolve():shutil.copy2(f,dest)
        url=mapped.get(local)
        if url:
            parsed=urlparse(url)
            if parsed.scheme!='https' or parsed.hostname not in ('mmbiz.qpic.cn','mmbiz.qlogo.cn'):
                raise ValueError('请使用微信上传返回的HTTPS图片地址：'+str(url))
        if not any(m['local']==local for m in manifest):manifest.append({'local':local,'source':str(f),'role':role,'wechat_url':url})
        img_style='display:block;width:100%;max-width:100%;height:auto;margin:0 auto;border:0;'
        if width:img_style+=f'max-width:{int(width)}px;'
        return '<img src="'+html.escape(local,quote=True)+'" alt="'+html.escape(alt,quote=True)+'" style="'+img_style+'" />'
    def runs(rr):
        parts=[]
        for r in rr:
            text=html.escape(str(r.get('text',''))).replace('\n','<br />').replace('\t','&#8195;')
            if r.get('bold'):text='<strong style="font-weight:700;">'+text+'</strong>'
            if r.get('italic'):text='<em>'+text+'</em>'
            if r.get('underline'):text='<span style="text-decoration:underline;">'+text+'</span>'
            if r.get('href'):text='<a href="'+html.escape(safe_href(r['href']),quote=True)+'" style="color:'+theme['primary']+';text-decoration:underline;">'+text+'</a>'
            parts.append(text)
        return ''.join(parts)
    count=0
    def block(b):
        nonlocal count
        typ=b['type'];text=runs(b.get('runs',[]));primary=theme['primary'];light=theme['light'];accent=theme['accent']
        if typ=='group':
            children=''.join(block(x) for x in b['blocks'])
            variant=b.get('variant','section')
            bg=light if variant=='summary' else '#ffffff'
            border=theme.get('group_border')
            if border:
                if not re.fullmatch(r'#[0-9a-fA-F]{6}',border):raise ValueError('分区边框颜色须为六位色值')
                padding=int(theme.get('summary_padding',22) if variant=='summary' else theme.get('group_padding',15))
                if not 0<=padding<=48:raise ValueError('框内留白须为0–48px')
                rounding='border-top-left-radius:20px;border-bottom-right-radius:20px;' if variant=='intro' else ''
                return f'<section data-layout-group="{html.escape(variant,quote=True)}" style="box-sizing:border-box;width:100%;margin:0 0 26px;padding:{padding}px;border:1px solid {border};{rounding}background:{bg};">{children}</section>'
            return f'<section style="box-sizing:border-box;width:100%;margin:0 0 26px;padding:18px 0 2px;background:{bg};">{children}</section>'
        if typ=='section_label':
            label=str(b['label'])
            if label not in a.get('layout_additions',[]):raise ValueError('新增分节标题必须记入layout_additions')
            return '<section data-generated="true">'+block({'type':'heading','level':2,'runs':[{'text':label}]})+'</section>'
        if typ=='end_mark':
            return f'<section data-generated="true" style="margin:26px 0 18px;text-align:center;font-size:13px;letter-spacing:3px;font-weight:700;color:{primary};">END</section>'
        if typ=='speaker':
            return f'<p style="margin:20px 0 10px;font-size:14px;font-weight:700;color:{primary};text-indent:0;">{text}</p>'
        if typ=='heading':
            level=b.get('level',2)
            if level>=3:return f'<section style="margin:22px 0 12px;font-size:16px;font-weight:700;color:{primary};">{text}</section>'
            count+=1
            if theme['heading']=='section-label':
                ornaments=f'<span data-generated="true" style="display:inline-block;width:7px;height:7px;margin:0 9px;background:{accent};vertical-align:middle;"></span>'
                return f'<section style="text-align:center;margin:28px 0 16px;font-size:16px;font-weight:700;">{ornaments}<span style="display:inline-block;padding:6px 18px;background:{primary};color:#ffffff;">{text}</span>{ornaments}</section>'
            if theme['heading']=='number':
                label='<span data-generated="true" style="display:inline-block;padding:3px 9px;margin-right:10px;border-radius:20px;background:'+accent+';color:#ffffff;">'+f'{count:02d}'+'</span>'
                return f'<section style="margin:28px 0 16px;font-size:16px;font-weight:700;color:{primary};">{label}{text}</section>'
            return f'<section style="margin:28px 0 16px;padding:7px 12px;background:{light};color:{primary};font-size:16px;font-weight:700;">{text}</section>'
        if typ=='component':
            key=b['component']
            if key not in COMPONENTS:raise ValueError('未知品牌组件：'+key)
            meta=COMPONENTS[key]
            if key=='qrcode-unlabeled':warnings.append('选用了未标注归属的二维码，需核对目标账号。')
            source=b.get('src') or str(SKILL_DIR/meta['file'])
            bg=b.get('background') or ('#bd3434' if meta['background'] in ('dark','red') else '#ffffff')
            if not re.fullmatch(r'#[0-9a-fA-F]{6}',bg):raise ValueError('组件背景须为六位色值')
            img=image(source,'component:'+key,meta['label'],b.get('width',meta['display_width']))
            caption='<p style="text-align:center;font-size:12px;color:#858585;margin:10px 0 0;">'+html.escape(b['caption'])+'</p>' if b.get('caption') else ''
            padding='0' if b.get('edge_aligned') else '12px'
            return '<section style="margin:20px 0;padding:'+padding+';background:'+bg+';">'+img+caption+'</section>'
        if typ=='image':
            img=image(b['src'],b.get('role','content'),b.get('alt',''),b.get('width'))
            caption='<section style="margin-top:10px;text-align:center;font-size:12px;color:#858585;">'+html.escape(b['caption'])+'</section>' if b.get('caption') else ''
            percent=float(b.get('width_percent',90))
            if not 10<=percent<=100:raise ValueError('图片宽度百分比须在10–100之间')
            return f'<section style="margin:16px auto;width:{percent:g}%;">'+img+caption+'</section>'
        if typ=='gallery':
            # Stacking is intentionally the stable default; scrolling is opt-in.
            if b.get('mode','stack')=='scroll':
                warnings.append('滑动图集需在Z0导入、保存后用微信手机预览验证。')
                slides=''.join('<section style="display:inline-block;width:100%;vertical-align:top;white-space:normal;">'+block({'type':'image',**im})+'</section>' for im in b['images'])
                return '<section style="width:100%;overflow-x:auto;white-space:nowrap;">'+slides+'</section><p data-generated="true" style="margin:10px 0;text-align:center;font-size:12px;color:#858585;">左右滑动查看更多</p>'
            return ''.join(block({'type':'image',**im}).replace('margin:16px auto','margin:10px auto') for im in b['images'])
        if typ=='table':
            rows=[]
            widths=b.get('column_widths',[])
            if widths and (any(float(w)<=0 for w in widths) or abs(sum(float(w) for w in widths)-100)>0.1):raise ValueError('表格列宽须为合计100的正数百分比')
            for row_index,row in enumerate(b['rows']):
                cells=[]
                for cell_index,c in enumerate(row):
                    content=''.join(block(x) for x in c['blocks'])
                    if cell_index in b.get('nowrap_name_columns',[]) and row_index>=int(b.get('header_rows',0)):
                        chunks=[]
                        for paragraph in c['blocks']:
                            if paragraph['type']!='paragraph':chunks.append(block(paragraph));continue
                            pieces=[]
                            for run in paragraph.get('runs',[]):
                                for part in re.split('(、)',run.get('text','')):
                                    rendered=runs([{**run,'text':part}])
                                    if re.fullmatch(r'[\u4e00-\u9fff]{2,4}',part):rendered='<span style="white-space:nowrap;display:inline-block;">'+rendered+'</span>'
                                    pieces.append(rendered)
                            name_markup=''.join(pieces).replace('</span>、','、</span>')
                            chunks.append('<p style="margin:0;text-indent:0;">'+name_markup+'</p>')
                        content=''.join(chunks)
                    content=content.replace('text-indent:2em','text-indent:0').replace('margin:0 0 16px','margin:0')
                    header=row_index<int(b.get('header_rows',0))
                    extra=f'background:{light};color:{primary};' if header else 'background:#ffffff;'
                    if widths and cell_index<len(widths):extra+=f'width:{float(widths[cell_index]):g}%;'
                    cells.append(f'<td colspan="{int(c.get("colspan",1))}" rowspan="{int(c.get("rowspan",1))}" style="border:1px solid #d9e0ea;padding:9px 5px;vertical-align:middle;word-break:break-word;{extra}">{content}</td>')
                rows.append('<tr>'+''.join(cells)+'</tr>')
            return '<table style="border-collapse:collapse;width:100%;table-layout:fixed;margin:18px 0;font-size:13px;letter-spacing:0;line-height:1.6;">'+''.join(rows)+'</table>'
        if typ=='intro':return f'<section style="padding:18px 16px;margin:16px 0 24px;background:{light};border-radius:3px;text-align:justify;">{text}</section>'
        if typ=='quote':return f'<section style="padding:12px 16px;margin:18px 0;border-left:3px solid {primary};background:{light};">{text}</section>'
        if typ=='caption':return '<p style="margin:6px 0 18px;font-size:12px;color:#858585;text-align:center;">'+text+'</p>'
        if typ=='credit':return '<p style="margin:0;padding:5px 0;background:transparent;text-align:center;font-size:12px;color:#858585;">'+text+'</p>'
        if typ=='list_item':
            marker=html.escape(str(b.get('marker','•')))
            level=max(0,min(5,int(b.get('level',0))))
            return f'<p style="margin:8px 0;padding-left:{level*12}px;text-align:justify;"><span data-generated="true">{marker} </span>{text}</p>'
        if typ=='paragraph':
            indent='0' if b.get('indent',True) is False else '2em'
            return f'<p style="margin:0 0 16px;text-align:justify;text-indent:{indent};overflow-wrap:break-word;">{text}</p>'
        raise ValueError('未知内容模块：'+str(typ))
    body=''.join(block(b) for b in a['blocks'])
    heading='<h1 style="font-size:22px;line-height:1.4;margin:0 0 24px;">'+html.escape(a['title'])+'</h1>' if include_title else ''
    fragment=f'<section style="box-sizing:border-box;padding:0 10px;font-size:{theme["font_size"]:g}px;line-height:{theme["line_height"]:g};letter-spacing:{theme["letter_spacing"]:g}px;color:{theme["text"]};">'+heading+body+'</section>'
    if theme.get('page_background'):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',theme['page_background']):raise ValueError('背景色必须为六位色值')
        fragment=fragment.replace('padding:0 10px;',f'padding:16px 10px;background:{theme["page_background"]};',1)
    parsed=BeautifulSoup(fragment,'html.parser')
    for generated in parsed.select('[data-generated]'):generated.decompose()
    expected=(a['title'] if include_title else '')+blocks_text(a['blocks'])
    if compact(parsed.get_text())!=compact(expected):raise ValueError('渲染后的正文文本与结构稿不同；已停止交付')
    imported=fragment
    for entry in manifest:
        if entry['wechat_url']:imported=imported.replace('src="'+entry['local']+'"','src="'+html.escape(entry['wechat_url'],quote=True)+'"')
    (out/'article.html').write_text(imported,encoding='utf-8')
    preview='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+html.escape(a['title'])+'''</title><style>body{margin:0;background:#edf1f5;color:#273952;font-family:Arial,'Microsoft YaHei',sans-serif}.tools{max-width:680px;margin:20px auto;padding:0 16px;font-size:14px;line-height:1.8}button{background:#35558a;color:white;border:0;padding:9px 18px;border-radius:5px;cursor:pointer}article{max-width:430px;box-sizing:border-box;margin:20px auto;padding:24px 20px;background:white;box-shadow:0 8px 24px #25385012}.title{max-width:430px;margin:20px auto;font-size:20px;line-height:1.5;padding:0 20px;box-sizing:border-box}@media(max-width:480px){article{margin:0;box-shadow:none;width:100%}}</style><div class="tools"><strong>'''+html.escape(column+' · '+a.get('subtype',''))+'''</strong><br>这是本地排版预览。主标题请填入公众号标题栏；正文图片需由编辑器接收或上传到微信。<br><button onclick="copyBody()">复制排版正文</button> <span id="status"></span></div><h1 class="title">'''+html.escape(a['title'])+'''</h1><article id="article">'''+fragment+'''</article><script>function copyBody(){const el=document.getElementById('article');const range=document.createRange();range.selectNodeContents(el);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);let ok=false;try{ok=document.execCommand('copy')}catch(e){}document.getElementById('status').textContent=ok?'已复制，请在编辑器粘贴并检查图片。':'请手动复制选中的正文。';if(ok)selection.removeAllRanges();}</script></html>'''
    (out/'preview.html').write_text(preview,encoding='utf-8')
    if not a.get('classification_reviewed'):warnings.append('栏目为自动建议，尚需结合正文确认。')
    missing=[m['local'] for m in manifest if not m['wechat_url']]
    if missing:warnings.append('图片仍使用本地路径：交由编辑器接收/上传后才能成为公众号可发布稿。')
    checks={'column':column,'subtype':a.get('subtype'),'theme':theme_name,'classification_reviewed':a.get('classification_reviewed',False),'text_preserved':True,'source_text_changed_with_authorization':source_changed,'image_files':len(manifest),'images_pending_wechat_upload':missing,'z0_import_verified':False,'warnings':list(dict.fromkeys(warnings))}
    checks['layout_additions']=a.get('layout_additions',[])
    portable=json.loads(json.dumps(a))
    lookup={m['source']:m['local'] for m in manifest}
    def localize(blocks):
        for b in blocks:
            if b['type']=='group':localize(b['blocks'])
            elif b['type']=='component':
                f=Path(b.get('src') or str(SKILL_DIR/COMPONENTS[b['component']]['file']))
                if not f.is_absolute():f=(path.parent/f).resolve()
                b['src']=lookup[str(f)]
            elif b['type']=='image':
                f=Path(b['src']);f=f if f.is_absolute() else (path.parent/f).resolve()
                b['src']=lookup[str(f)]
            elif b['type']=='gallery':
                for im in b['images']:
                    f=Path(im['src']);f=f if f.is_absolute() else (path.parent/f).resolve()
                    im['src']=lookup[str(f)]
            elif b['type']=='table':
                for row in b['rows']:
                    for cell in row:localize(cell['blocks'])
    localize(portable['blocks'])
    dump(out/'checks.json',checks);dump(out/'image-manifest.json',manifest);dump(out/'image-map.template.json',{m['local']:m['wechat_url'] or '' for m in manifest});dump(out/'article.json',portable)
    publication={'title':a['title'],'summary':a.get('summary'),'cover':a.get('cover'),'cover_ratios':{'primary':'2.35:1','secondary':'1:1'},'target':'Z0 HTML导入微信公众号后台','import_tested':False}
    dump(out/'publication.json',publication)
    if not a.get('summary'):
        checks['warnings'].append('缺少摘要：请根据原稿拟定并核对，在公众号摘要栏填写。');dump(out/'checks.json',checks)
    (out/'导入说明.txt').write_text('栏目：'+column+' / '+a.get('subtype','')+'\n主标题：'+a['title']+'\n\n目标流程：HTML → Z0编辑器 → 微信公众号后台，不使用秀米。\narticle.html：用于Z0 HTML导入的正文片段，内联样式，不含预览工具栏或脚本。\npreview.html：本地预览，可复制正文作为辅助方式。\nimages：配套图片，不要丢弃。\npublication.json：标题、摘要、封面信息，另填后台对应栏目。\n\nZ0接收本地图片/上传后的实际行为尚待实测。图片须由编辑器接收或上传微信，本地路径不是可发布地址。可将微信返回的地址填入image-map.template.json，使用render --image-map重新生成。\n导入后保存草稿，手机预览核对文字、图片、图集、二维码和署名。本工具不自动登录、上传、写草稿或发布。\n',encoding='utf-8')
    return checks

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    e=sub.add_parser('extract');e.add_argument('source');e.add_argument('--out',required=True)
    r=sub.add_parser('render');r.add_argument('article');r.add_argument('--out',required=True);r.add_argument('--theme',choices=THEMES);r.add_argument('--image-map');r.add_argument('--include-title',action='store_true')
    c=sub.add_parser('classify');c.add_argument('title');c.add_argument('--source-column')
    args=p.parse_args()
    if args.cmd=='extract':result=extract(args.source,args.out);print(json.dumps({'title':result['title'],'classification':result['classification'],'blocks':len(result['blocks']),'warnings':result['warnings']},ensure_ascii=False))
    elif args.cmd=='render':print(json.dumps(render(args.article,args.out,args.theme,args.image_map,args.include_title),ensure_ascii=False))
    else:print(json.dumps(classify(args.title,source_column=args.source_column),ensure_ascii=False))

if __name__=='__main__':
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    try:main()
    except (ValueError,FileNotFoundError) as e:
        print('ERROR: '+str(e),file=sys.stderr);sys.exit(2)
