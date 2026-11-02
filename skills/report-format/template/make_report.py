"""Korean 관공서-style monochrome report builder (HTML -> PDF via headless Chrome).

Library use:
    from make_report import *
    html = document(header="PR #n 검토 보고", kind="검 토 보 고 서",
                    title="예시 제목", date="2026-11-01", author="기안자 이름", approver="결재자 이름",
                    approver_note="merge 대기", url="https://example.com/review", target="예시 저장소",
                    body=summary([...]) + chg([...], [...]) + section("1. 개요", table(...)) + ...)
    render(html, "보고-제목_검토보고서.pdf"); print(verify("보고-제목_검토보고서.pdf"))
CLI:
    python3 make_report.py example_content.py out.pdf      # content module must define HTML (str)
"""
import html as _h, os, re, subprocess, sys, tempfile, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(HERE, 'report.css'), encoding='utf-8').read()
ALLOWED_FONTS = ('NotoSansCJK', 'NotoSerifCJK', 'GothicA1')   # max 3 families; Gothic A1 only for ✔ ✖
# 판정 (verdict). 결재 상태(진행/반려/승인, approval-line/rules.json)와 다른 개념이다.
VERDICTS = {'ok': ('✔', '머지 가능'), 'done': ('✔', '머지 완료'), 'warn': ('▲', '확인 필요'), 'hold': ('✖', '보류')}
LEGEND = ('<div class="legend">판정 구분: <span class="mk">✔</span>머지 가능 · '
          '<span class="mk">▲</span>확인 필요 · <span class="mk">✖</span>보류</div>')

def esc(s): return _h.escape(s, quote=False)
def attr(s):
    """For a value inside a double-quoted attribute. Only `"` is replaced, so a value already passed through esc() is not escaped twice."""
    return s.replace('"', '&quot;')

def ul(items):
    """items: list of str (raw HTML) or (str, [children]) for a nested '-' level."""
    out = []
    for it in items:
        if isinstance(it, tuple): out.append(f'<li>{it[0]}{ul(it[1])}</li>')
        else: out.append(f'<li>{it}</li>')
    return '<ul>' + ''.join(out) + '</ul>'

def summary(items): return f'<div class="summary"><div class="cap">요 약</div>{ul(items)}</div>'

def chg(before, after):
    j = '<br>'.join
    return (f'<table class="chg"><caption>상태 변화</caption><tr class="before"><th>전에는</th><td>{j(before)}</td></tr>'
            f'<tr class="after"><th>이제는</th><td>{j(after)}</td></tr></table>')

def section(title, *parts): return f'<h2>{title}</h2>' + ''.join(parts)
def sub(title, *parts): return f'<h3>{title}</h3>' + ''.join(parts)
def note(text): return f'<p class="note">{text}</p>'

def table(headers, rows, widths=None, center=()):
    """headers: [str]; rows: [[cell html]]; widths: [css width or None]; center: column indexes to center."""
    w = widths or [None] * len(headers)
    th = ''.join(f'<th{" class=c" if i in center else ""}{f" style=width:{w[i]}" if w[i] else ""}>{h}</th>' for i, h in enumerate(headers))
    tr = ''.join('<tr>' + ''.join(f'<td{" class=c" if i in center else ""}>{c}</td>' for i, c in enumerate(r)) + '</tr>' for r in rows)
    return f'<table class="g"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'

def verdict(kind, url, items, order=None):
    """kind: ok | done | warn | hold. order: list of '권장 머지 순서' bullet strings (optional)."""
    mk, label = VERDICTS[kind]
    btn = '' if kind == 'done' else f'<a class="btn" href="{attr(url)}">머지하러 가기 →</a>'
    o = sub('권장 머지 순서', ul(order)) if order else ''
    return f'<div class="verdict"><div class="vrow"><div class="v"><span class="mk">{mk}</span>{label}</div>{btn}</div>{ul(items)}{LEGEND}{o}</div>'

def figure(title, src, caption, style='height:212mm', flow=False):
    """flow=True lets a short chart follow the text on the same page instead of starting a new one."""
    return f'<div class="fig{" flow" if flow else ""}"><h2>{title}</h2><img src="{src}" style="{style}"><div class="cap">{caption}</div></div>'

def head(kind, title, date, author, url, target, approver='', approver_note='', doc_no=None, sign=None):
    """doc_no: 문서번호 row (e.g. 보고-2026-0042). sign: a ready 결재란 table (approval-line) replacing the default box."""
    no = f'<tr><td class="k">문서번호</td><td colspan="3">{doc_no}</td></tr>' if doc_no else ''
    sign = sign or (f'<table class="sign"><tr><td class="side" rowspan="2">결재</td><th>기안</th><th>결재</th></tr>'
                    f'<tr><td>{author}</td><td>{approver}<br><span class="note">{approver_note}</span></td></tr></table>')
    return (f'<div class="kind">{kind}</div><div class="titlebox"><h1>{title}</h1></div>'
            f'<div class="headrow"><table class="meta">{no}<tr><td class="k">기안일</td><td>{date}</td>'
            f'<td class="k" style="padding-left:6mm">기안</td><td>{author}</td></tr>'
            f'<tr><td class="k">대상</td><td colspan="3"><a href="{attr(url)}">{target}</a></td></tr></table>'
            f'{sign}</div>')

def thead_fix(html):
    """Wrap the first header row of each table.g in <thead> so it repeats when a table breaks across pages."""
    return re.sub(r'(<table class="g">)\s*(<tr>(?:(?!</tr>).)*?<th.*?</tr>)', r'\1<thead>\2</thead>', html, flags=re.S)

def document(header, body, extra_css='', **h):
    body = thead_fix(body)
    css = CSS.replace('@@HEADER@@', header) + extra_css
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body>{head(**h)}{body}</body></html>'

def chrome_bin():
    """The stable binary. A `google-chrome` wrapper that joins a shared profile with a debug port may never exit."""
    for name in ('google-chrome-stable', 'google-chrome'):
        found = shutil.which(name)
        if found: return found
    raise SystemExit('google-chrome을 찾지 못했습니다.')

def chrome_flags(profile, pdf, hp):
    """Chrome will not start as root with its sandbox on, so the sandbox is turned off for root only."""
    root = getattr(os, 'geteuid', lambda: -1)() == 0
    return ['--headless=new', *(['--no-sandbox'] if root else []), '--disable-gpu', '--no-pdf-header-footer',
            f'--user-data-dir={profile}', f'--print-to-pdf={pdf}', 'file://' + hp]

def render(html, pdf, assets=(), html_path=None):
    """Write html next to its assets (charts) and print to PDF with headless Chrome in a throwaway profile.
    html_path: where the HTML document is kept (default: hidden `.name.html` next to the PDF)."""
    pdf = os.path.abspath(pdf); d = os.path.dirname(pdf); os.makedirs(d, exist_ok=True)
    for a in assets: shutil.copy(a, d)
    hp = os.path.abspath(html_path or os.path.join(d, '.' + os.path.splitext(os.path.basename(pdf))[0] + '.html'))
    open(hp, 'w', encoding='utf-8').write(html)
    if os.path.exists(pdf): os.remove(pdf)
    profile = tempfile.mkdtemp(prefix='report-chrome-')
    try:
        proc = subprocess.run([chrome_bin(), *chrome_flags(profile, pdf, hp)],
                              stderr=subprocess.DEVNULL, check=False, timeout=180)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if proc.returncode != 0 or not os.path.exists(pdf):
        raise SystemExit('PDF를 만들지 못했습니다.')
    return pdf

def verify(pdf, png_dir=None, dpi=110):
    """Pages, size, fonts (only allowed families => no tofu fallback), max chroma per page, link URLs."""
    import numpy as np; from PIL import Image
    pages = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
    fonts = sorted({l.split()[0].split('+')[-1] for l in subprocess.run(['pdffonts', pdf], capture_output=True, text=True).stdout.splitlines()[2:] if l.strip()})
    bad = [f for f in fonts if not f.startswith(ALLOWED_FONTS)]
    urls = sorted(set(re.findall(r'(https?://\S+)', subprocess.run(['pdfinfo', '-url', pdf], capture_output=True, text=True).stdout)))
    png_dir = png_dir or tempfile.mkdtemp(); os.makedirs(png_dir, exist_ok=True)
    stem = os.path.join(png_dir, re.sub(r'\W+', '_', os.path.basename(pdf))[:40])
    subprocess.run(['pdftoppm', '-r', str(dpi), '-png', pdf, stem], check=True)
    chroma, fill = [], []
    for f in sorted(glob.glob(stem + '-*.png')):
        a = np.asarray(Image.open(f).convert('RGB')).astype(int)
        chroma.append(int((a.max(2) - a.min(2)).max()))
        rows = np.where((a.min(2) < 200).any(1))[0]          # ink rows, minus header/footer bands
        body = rows[(rows > a.shape[0] * 0.06) & (rows < a.shape[0] * 0.93)]
        fill.append(round(float((body.max() - a.shape[0] * 0.06) / (a.shape[0] * 0.87)), 2) if len(body) else 0.0)
        Image.open(f).convert('L').save(f.replace('.png', '-gray.png'))
    return dict(pdf=pdf, bytes=os.path.getsize(pdf), pages=pages, fonts=fonts, disallowed_fonts=bad,
                max_chroma=max(chroma), page_fill=fill, urls=urls, png_dir=png_dir)

if __name__ == '__main__':
    ns = {}; exec(open(sys.argv[1], encoding='utf-8').read(), ns)
    out = render(ns['HTML'], sys.argv[2], ns.get('ASSETS', ()))
    print(verify(out))
