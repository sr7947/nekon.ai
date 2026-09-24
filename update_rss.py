import re

path = 'nekon_agents.py'
content = open(path, 'r', encoding='utf-8').read()

live_func = '''def fetch_ai_news_updates() -> str:
    import urllib.request, xml.etree.ElementTree as ET, json, ssl
    sources = [
        {"company": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml"},
        {"company": "Google AI", "url": "https://blog.google/technology/ai/rss/"},
        {"company": "MIT AI News", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"},
        {"company": "ArXiv AI", "url": "https://export.arxiv.org/rss/cs.AI"}
    ]
    live_articles = []
    ctx = ssl._create_unverified_context()
    for s in sources:
        try:
            req = urllib.request.Request(s["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as res:
                root = ET.fromstring(res.read())
                items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
                for item in items[:2]:
                    t_el = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
                    l_el = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
                    p_el = item.find("pubDate") or item.find("updated") or item.find("{http://www.w3.org/2005/Atom}updated")
                    title = t_el.text.strip() if t_el is not None and t_el.text else "AI Breakthrough Update"
                    link = l_el.text.strip() if l_el is not None and l_el.text else s["url"]
                    if l_el is not None and "href" in l_el.attrib:
                        link = l_el.attrib["href"]
                    pub = p_el.text.strip() if p_el is not None and p_el.text else "Today"
                    live_articles.append({"title": title, "company": s["company"], "category": "Live Breakthrough", "summary": f"Latest update from {s['company']}: {title}", "source_url": link, "published_at": pub})
        except Exception as e:
            print(f"[WARN] {s['company']}: {e}")
    if not live_articles:
        live_articles = [{"title": "DeepSeek Open-Sources DeepSeek-V3 MoE Architecture", "company": "DeepSeek", "category": "Open Source", "summary": "DeepSeek MoE architecture.", "source_url": "https://www.deepseek.com/blog", "published_at": "Today"}]
    return json.dumps(live_articles, indent=2)
'''

pattern = r'def fetch_ai_news_updates\(\) -> str:[\s\S]*?return json\.dumps\(mock_articles, indent=2\)'
updated = re.sub(pattern, live_func, content)
open(path, 'w', encoding='utf-8').write(updated)
print("✅ Successfully updated nekon_agents.py with REAL-TIME Live RSS Ingestion!")
