# from https://search.byrdocs.org/llms.txt

import httpx
import asyncio
from urllib.parse import urljoin
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright             # type: ignore[import error]

try:
    from .main import logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

SEARCH_URL = "https://search.byrdocs.org/api/search"

async def search_byrdocs(keyword=None, type_="all", jmespath=None,
                   limit=20, shorten=False, token=None):
    payload = {}
    if keyword:
        payload["keyword"] = keyword
    if type_ and type_ != "all":        # "book" | "doc" | "test" | "all"
        payload["type"] = type_
    if jmespath:
        payload["jmespath"] = jmespath
    if limit:
        payload["limit"] = limit
    if shorten:
        payload["shorten"] = shorten

    headers = {"content-type": "application/json"}
    if token:
        headers["authorization"] = f"Bearer {token}"

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(SEARCH_URL, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

async def query_byrdocs_guide(query: str, site_url: str = "https://guide.byrdocs.org/") -> List[Dict[str, Any]]:
    """
    使用 Playwright 调用基于 Pagefind 的静态站点搜索 API。
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(site_url, wait_until="networkidle")

            # 1. 优先尝试标准路径 /pagefind/pagefind.js
            # 2. 如果失败，再扫描页面中的 <script> 标签自动探测
            pagefind_script_path = page.evaluate("""() => {
                // 方法1：先检查标准路径是否存在
                return new Promise((resolve) => {
                    fetch('/pagefind/pagefind.js')
                        .then(res => {
                            if (res.ok) {
                                resolve('/pagefind/pagefind.js');
                            } else {
                                // 方法2：扫描所有 <script> 标签
                                const scripts = Array.from(document.querySelectorAll('script'))
                                    .filter(s => s.src && s.src.includes('pagefind'));
                                if (scripts.length > 0) {
                                    resolve(new URL(scripts[0].src, window.location.origin).pathname);
                                } else {
                                    // 方法3：尝试常见变体路径
                                    fetch('/_pagefind/pagefind.js')
                                        .then(res2 => {
                                            if (res2.ok) resolve('/_pagefind/pagefind.js');
                                            else resolve(null);
                                        })
                                        .catch(() => resolve(null));
                                }
                            }
                        })
                        .catch(() => {
                            // fetch 失败，回退到扫描 <script> 标签
                            const scripts = Array.from(document.querySelectorAll('script'))
                                .filter(s => s.src && s.src.includes('pagefind'));
                            resolve(scripts.length > 0 
                                ? new URL(scripts[0].src, window.location.origin).pathname 
                                : null);
                        });
                });
            }""")

            if not pagefind_script_path:
                logger.warning("Warning: Could not find Pagefind script.")
                return []

            logger.info(f"Found Pagefind script at: {pagefind_script_path}")

            # 执行搜索
            results = page.evaluate("""
                async ({ query, scriptPath }) => {
                    try {
                        const pagefind = await import(scriptPath);
                        await pagefind.init();
                        const search = await pagefind.search(query);
                        const dataPromises = search.results.slice(0, 15).map(r => r.data());
                        const data = await Promise.all(dataPromises);
                        return data.map(r => ({
                            url: r.url,
                            title: r.meta?.title || '',
                            excerpt: r.excerpt || ''
                        }));
                    } catch (e) {
                        console.error("Search execution error:", e);
                        return [];
                    }
                }
            """, {"query": query, "scriptPath": pagefind_script_path})

            if not results:
                return []

            formatted_results = []
            for item in results:
                full_url = urljoin(site_url, item.get("url", ""))
                formatted_results.append({
                    "url": full_url,
                    "title": item.get("title", "").strip(),
                    "excerpt": item.get("excerpt", "").strip()
                })

            return formatted_results

    except Exception as e:
        logger.error(f"Error during search: {e}")
        return []

if __name__ == "__main__":
    search_results = asyncio.run(query_byrdocs_guide(query="校园卡"))
    if search_results:
        logger.info(f"Total results: {len(search_results)}")
        for res in search_results:
            logger.info(f"- [{res['title']}]")
            logger.info(f"  ...{res['excerpt']}...")
            logger.info(f"  url: {res["url"]}")
    else:
        logger.error("No results found or an error occurred.")

    # 示例 1：搜索高等数学教材
    r = asyncio.run(search_byrdocs(keyword="Advanced Mathematics", type_="all", limit=3))
    logger.info("总数:", r["total"])
    for item in r["results"]:
        logger.info(item["data"]["title"], "->", item["url"])
    ret = asyncio.run(search_byrdocs(keyword="Advanced Mathematics", type_="all", limit=3, jmespath="[].{data: data, url:url}"))
    logger.info(ret)