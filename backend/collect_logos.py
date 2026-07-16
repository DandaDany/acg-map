#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect venue logos from official domains.

Modes:
  python3 backend/collect_logos.py              # batch, high-confidence only
  python3 backend/collect_logos.py example.com  # single domain, high-confidence only
  python3 backend/collect_logos.py --debug example.com
  python3 backend/collect_logos.py --force example.com  # download best candidate even if low confidence
"""
import json, os, re, sys, subprocess, tempfile, time
from paths import path as P

HERE = os.path.dirname(os.path.abspath(__file__))
LOGODIR = P("logos"); os.makedirs(LOGODIR, exist_ok=True)
MAPP = P("logo_map.json")
DEBUGDIR = P("_logo_debug"); os.makedirs(DEBUGDIR, exist_ok=True)

def slug(dom): return re.sub(r'[^a-z0-9]+', '_', dom.lower()).strip('_')
def load_json_retry(path, default, tries=5, delay=0.4):
    last = None
    for i in range(tries):
        try:
            if not os.path.exists(path):
                return default
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
            last = e
            if i == tries - 1:
                break
            time.sleep(delay * (i + 1))
    if isinstance(last, FileNotFoundError):
        return default
    raise last

def dump_json_atomic(obj, path):
    folder = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + ".", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        os.chmod(path, 0o644)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass

def ext_of(url, content_type=""):
    m = re.search(r'\.(svg|png|jpe?g|webp|ico)(?:[?#]|$)', url, re.I)
    if m: return "." + m.group(1).lower().replace("jpeg", "jpg")
    if "svg" in content_type: return ".svg"
    if "jpeg" in content_type: return ".jpg"
    if "webp" in content_type: return ".webp"
    if "icon" in content_type: return ".ico"
    return ".png"

FIND = r"""
() => {
  const bad=/(loading|spinner|sociallink|social|facebook|line|instagram|youtube|twitter|search|menu|hamburger|btn|sprite|blank|pixel|qrcode|footer|banner|kv|poster)/i;
  const logoHint=/(logo|brand|商標|標誌|識別|site.?title|navbar.?brand|header.?logo|logoimg|logotype)/i;
  const abs=(u)=>{try{return new URL(u, location.href).href}catch(e){return ''}};
  const fromSrcset=(s)=>s?String(s).split(',').map(x=>x.trim().split(/\s+/)[0]).filter(Boolean).pop():'';
  const out=[];
  const push=(kind,src,attrs,r,w,h)=>{
    src=abs(src); attrs=String(attrs||'');
    const reasons=[];
    const hint=logoHint.test(attrs+' '+src);
    if(!src) reasons.push('empty-src');
    if(src && bad.test(src+' '+attrs)) reasons.push('bad-word');
    if(w<24||h<12) reasons.push('too-small');
    if(!hint && (w>1400||h>700)) reasons.push('too-large');
    if(r.top>420) reasons.push('too-low');
    let score=Math.max(1,w)*Math.max(1,h);
    if(hint) score*=12;
    if(r.top<160) score*=2;
    if(/\.(svg)(?:[?#]|$)/i.test(src)) score*=1.5;
    if(kind==='favicon') score*=0.7;
    if(!hint && kind!=='favicon') reasons.push('no-logo-hint');
    out.push({kind,src,attrs:attrs.slice(0,180),top:Math.round(r.top),w:Math.round(w),h:Math.round(h),hint,score:Math.round(score),reasons});
  };
  document.querySelectorAll('img,svg image').forEach(el=>{
    const r=el.getBoundingClientRect();
    const w=el.naturalWidth||r.width||80, h=el.naturalHeight||r.height||30;
    const src=el.currentSrc||el.href?.baseVal||el.src||el.getAttribute('data-src')||fromSrcset(el.getAttribute('srcset'))||'';
    const attrs=[el.className,el.id,el.alt,el.title,src].join(' ');
    push('img',src,attrs,r,w,h);
  });
  document.querySelectorAll('header,nav,.header,.navbar,.brand,.logo,[class*="logo"],[id*="logo"]').forEach(el=>{
    const r=el.getBoundingClientRect();
    const attrs=[el.className,el.id,el.getAttribute('aria-label'),el.textContent].join(' ');
    const bg=getComputedStyle(el).backgroundImage||'';
    const m=bg.match(/url\(["']?([^"')]+)/);
    if(m) push('background',m[1],attrs,r,Math.max(80,r.width),Math.max(30,r.height));
  });
  document.querySelectorAll('link[rel]').forEach(el=>{
    const rel=(el.getAttribute('rel')||'').toLowerCase();
    if(!/(icon|apple-touch-icon)/.test(rel)) return;
    push('favicon',el.href,rel,{top:0},96,96);
  });
  out.sort((a,b)=>
    Number(b.hint)-Number(a.hint) ||
    a.reasons.length-b.reasons.length ||
    b.score-a.score
  );
  return out.slice(0,60);
}
"""

def _download(pg, dom, cand):
    r = pg.request.get(cand["src"], timeout=15000)
    if not r.ok: return None, f"http-{r.status}"
    body = r.body()
    ctype = (r.headers.get("content-type") or "").lower()
    if not (ctype.startswith("image/") or "svg" in ctype or re.search(r'\.(svg|png|jpe?g|webp|ico)(?:[?#]|$)', cand["src"], re.I)):
        return None, "not-image"
    if len(body) <= (80 if cand.get("kind") == "favicon" else 500):
        return None, "tiny-body"
    fn = slug(dom) + ext_of(cand["src"], ctype)
    path = os.path.join(LOGODIR, fn)
    open(path, "wb").write(body)
    return "logos/" + fn, ""

def run_single(dom, debug=False, force=False):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width":1366,"height":900}, ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")
        pg = ctx.new_page()
        hosts = [dom] if dom.startswith("www.") else ["www."+dom, dom]
        loaded_url = ""
        load_errors = []
        for host in hosts:
            try:
                pg.goto("https://" + host, wait_until="commit", timeout=25000)
                try:
                    pg.wait_for_load_state("domcontentloaded", timeout=6000)
                except Exception:
                    pass
                pg.wait_for_timeout(2200)
                loaded_url = pg.url
                break
            except Exception as e:
                load_errors.append({"url": "https://" + host, "error": type(e).__name__, "message": str(e)[:240]})
                if "Timeout" in type(e).__name__:
                    try:
                        pg.wait_for_timeout(2200)
                        if pg.evaluate("() => !!document.body"):
                            loaded_url = pg.url
                            break
                    except Exception:
                        pass
                continue
        if not loaded_url:
            if debug:
                dbg = {"domain": dom, "loaded_url": "", "load_errors": load_errors, "candidates": []}
                path = os.path.join(DEBUGDIR, slug(dom) + ".json")
                json.dump(dbg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(json.dumps(dbg, ensure_ascii=False, indent=1))
            b.close(); print("MISS"); return
        cands = pg.evaluate(FIND)
        if debug:
            dbg = {"domain": dom, "loaded_url": loaded_url, "load_errors": load_errors, "candidates": cands}
            path = os.path.join(DEBUGDIR, slug(dom) + ".json")
            json.dump(dbg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(json.dumps(dbg, ensure_ascii=False, indent=1))
        usable = [c for c in cands if not c["reasons"] or c["reasons"] == ["no-logo-hint"] and c["kind"] == "favicon"]
        if force and not usable:
            usable = cands[:3]
        for cand in usable:
            try:
                got, err = _download(pg, dom, cand)
                if got:
                    print(got); b.close(); return
                if debug: print("DOWNLOAD_REJECT", cand.get("src"), err, file=sys.stderr)
            except Exception as e:
                if debug: print("DOWNLOAD_ERR", type(e).__name__, str(e)[:120], file=sys.stderr)
        b.close(); print("MISS")

def main():
    lmap = load_json_retry(P("venue_logos.json"), {}).get("map", [])
    domains = []
    for _kw, dom in lmap:
        if dom not in domains: domains.append(dom)
    out = load_json_retry(MAPP, {})
    for dom in domains:
        if dom.endswith(".manual"):
            continue
        if dom in out and os.path.exists(P(out[dom])): continue
        try:
            r = subprocess.run([sys.executable, __file__, dom], capture_output=True, text=True, timeout=45)
            line = (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else "MISS"
            if line.startswith("logos/"):
                out[dom] = line
                dump_json_atomic(out, MAPP)
                print("OK  ", dom, "->", line, file=sys.stderr)
            else:
                print("MISS", dom, file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("TIMEOUT", dom, file=sys.stderr)
        except Exception as e:
            print("ERR", dom, type(e).__name__, file=sys.stderr)
    print(json.dumps({"domains": len(domains), "got": len(out)}, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--debug":
        run_single(sys.argv[2], debug=True)
    elif len(sys.argv) >= 3 and sys.argv[1] == "--force":
        run_single(sys.argv[2], debug=True, force=True)
    elif len(sys.argv) == 2:
        run_single(sys.argv[1])
    else:
        main()
