import json
from crawl import PageData

def write_json_report(page_data: dict[str, PageData], filename="report.json") -> None:
    """
    Write the page data to a JSON file.

    Args:
        page_data (dict): A dictionary containing the extracted data for all crawled pages.
        filename (str): The name of the output JSON file. Defaults to "report.json".
    """
    pages = sorted(page_data.values(), key=lambda x: x["url"])

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
