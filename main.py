import asyncio
import sys
from crawl import crawl_site_async
from json_report import write_json_report

async def main():
    len_args = len(sys.argv)
    if len_args < 2:
        print("no website provided")
        sys.exit(1)

    elif len_args > 4:
        print("too many arguments provided")
        sys.exit(1)

    base_url = sys.argv[1]
    max_concurrency = int(sys.argv[2]) or 3
    max_pages = int(sys.argv[3]) or 10

    print(f"Starting async crawl of: {base_url}")

    page_data = await crawl_site_async(base_url, max_concurrency, max_pages)

    for page in page_data.values():
        print(f"Found {len(page['outgoing_links'])} outgoing links on {page['url']}")
    
    write_json_report(page_data, filename="report.json")


if __name__ == "__main__":
    asyncio.run(main())
