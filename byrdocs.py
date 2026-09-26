import asyncio
import logging
from urllib.parse import urljoin
from typing import List, Dict, Any

import httpx
from playwright.async_api import async_playwright           # type: ignore

try:
    from .main import logger
except ImportError:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

SEARCH_URL = "https://search.byrdocs.org/api/search"


async def search_byrdocs(
    keyword=None,
    type_="all",
    jmespath=None,
    limit=20,
    shorten=False,
    token=None,
):
    payload = {}
    if keyword:
        payload["keyword"] = keyword
    if type_ and type_ != "all":
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

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(SEARCH_URL, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def query_byrdocs_guide(
    query: str,
    site_url: str = "https://guide.byrdocs.org/",
) -> List[Dict[str, Any]]:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                page = await browser.new_page()
                await page.goto(site_url, wait_until="networkidle")

                pagefind_script_path = await page.evaluate(
                    """() => {
                        return new Promise((resolve) => {
                            fetch('/pagefind/pagefind.js')
                                .then(res => {
                                    if (res.ok) {
                                        resolve('/pagefind/pagefind.js');
                                    } else {
                                        const scripts = Array.from(document.querySelectorAll('script'))
                                            .filter(s => s.src && s.src.includes('pagefind'));
                                        if (scripts.length > 0) {
                                            resolve(new URL(scripts[0].src, window.location.origin).pathname);
                                        } else {
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
                                    const scripts = Array.from(document.querySelectorAll('script'))
                                        .filter(s => s.src && s.src.includes('pagefind'));
                                    resolve(
                                        scripts.length > 0
                                            ? new URL(scripts[0].src, window.location.origin).pathname
                                            : null
                                    );
                                });
                        });
                    }"""
                )

                if not pagefind_script_path:
                    logger.warning("Could not find Pagefind script.")
                    return []

                logger.info("Found Pagefind script at: %s", pagefind_script_path)

                results = await page.evaluate(
                    """
                    async ({ query, scriptPath }) => {
                        try {
                            const pagefind = await import(scriptPath);
                            if (pagefind.init) {
                                await pagefind.init();
                            }
                            const search = await pagefind.search(query);
                            const dataPromises = search.results
                                .slice(0, 15)
                                .map(r => r.data());
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
                    """,
                    {"query": query, "scriptPath": pagefind_script_path},
                )

                if not results:
                    return []

                formatted_results = []
                for item in results:
                    full_url = urljoin(site_url, item.get("url", ""))
                    formatted_results.append(
                        {
                            "url": full_url,
                            "title": item.get("title", "").strip(),
                            "excerpt": item.get("excerpt", "").strip(),
                        }
                    )

                return formatted_results

            finally:
                await browser.close()

    except Exception as e:
        logger.error("Error during search: %s", e)
        return []


if __name__ == "__main__":
    search_results = asyncio.run(query_byrdocs_guide(query="校园卡"))

    if search_results:
        logger.info("Total results: %s", len(search_results))
        for res in search_results:
            logger.info("- [%s]", res["title"])
            logger.info("  ...%s...", res["excerpt"])
            logger.info("  url: %s", res["url"])
    else:
        logger.error("No results found or an error occurred.")

    r = asyncio.run(
        search_byrdocs(keyword="Advanced Mathematics", type_="all", limit=3)
    )
    logger.info("总数: %s", r["total"])
    for item in r["results"]:
        logger.info("%s -> %s", item["data"]["title"], item["url"])

    ret = asyncio.run(
        search_byrdocs(
            keyword="Advanced Mathematics",
            type_="all",
            limit=3,
            jmespath="[].{data: data, url:url}",
        )
    )
    logger.info("%s", ret)