import asyncio
from urllib import response
from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup, Tag
from types import TracebackType
from typing import TypedDict
import requests
import aiohttp


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing the scheme (http:// or https://) and any trailing slashes.
    
    Args:
        url (str): The URL to normalize.
    
    Returns:
        str: The normalized URL.
    """

    split_url = urlsplit(url)
    normalized_url = split_url.netloc + split_url.path
    return normalized_url.rstrip('/').lower()


def get_heading_from_html(html: str) -> str:
    """
    Extract the first heading (h1 or h2) from the given HTML content.
    
    Args:
        html (str): The HTML content to parse.
    Returns:
        str: The text of the first heading found, or an empty string if no headings are present.
    """
    soup = BeautifulSoup(html, 'html.parser')
    heading = soup.find(['h1', 'h2'])
    return heading.get_text(strip=True) if isinstance(heading, Tag) else ''


def get_first_paragraph_from_html(html: str) -> str:
    """
    Extract the first paragraph from the given HTML content, prioritizing paragraphs within <main> tags.
    
    Args:
        html (str): The HTML content to parse.

    Returns:
        str: The text of the first paragraph found, or an empty string if no paragraphs are present.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # First, look for paragraphs within <main> tags
    main_tag = soup.find('main')

    if isinstance(main_tag, Tag):
        first_paragraph = main_tag.find('p')

    else:
        first_paragraph = soup.find('p')

    return first_paragraph.get_text(strip=True) if isinstance(first_paragraph, Tag) else ''


def get_urls_from_html(html, base_url) -> list[str]:
    """
    Extract all unique URLs from the given HTML content, resolving relative URLs against the base URL.
    
    Args:
        html (str): The HTML content to parse.
        base_url (str): The base URL to resolve relative URLs against.

    Returns:
        list: A list of unique URLs found in the HTML content.
    """

    soup = BeautifulSoup(html, 'html.parser')
    urls = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        urls.add(full_url)

    return list(urls)


def get_images_from_html(html, base_url) -> list[str]:
    """
    Extract all unique image URLs from the given HTML content, resolving relative URLs against the base URL.
    
    Args:
        html (str): The HTML content to parse.
        base_url (str): The base URL to resolve relative URLs against.
    
    Returns:
        list: A list of unique image URLs found in the HTML content.
    """
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = set()

    for img_tag in soup.find_all('img', src=True):
        src = img_tag['src']
        # Resolve relative URLs
        full_url = urljoin(base_url, src)
        image_urls.add(full_url)

    return list(image_urls)


def extract_page_data(html: str, page_url: str) -> PageData:
    """
    Extract the heading, first paragraph, URLs, and image URLs from the given HTML content.
    
    Args:
        html (str): The HTML content to parse.
        page_url (str): The URL of the page being parsed.
    
    Returns:
        dict: A dictionary containing the extracted data.
    """
    heading = get_heading_from_html(html)
    first_paragraph = get_first_paragraph_from_html(html)
    outgoing_links = get_urls_from_html(html, page_url)
    image_urls = get_images_from_html(html, page_url)

    return {
        "url": page_url,
        "heading": heading,
        "first_paragraph": first_paragraph,
        "outgoing_links": outgoing_links,
        "image_urls": image_urls,
    }



class AsyncCrawler:
    """
    A class to perform asynchronous crawling of web pages.
    """

    def __init__(self, base_url: str, max_concurrency: int, max_pages: int):
        self.base_url = base_url
        self.base_domain = urlsplit(base_url).netloc
        self.page_data: dict[str, PageData] = {}
        self.visited: set[str] = set()
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session: aiohttp.ClientSession | None = None
        self.max_pages = max_pages
        self.should_stop = False
        self.all_tasks: set[asyncio.Task] = set()

    async def __aenter__(self) -> "AsyncCrawler":
        self.session = aiohttp.ClientSession()
        return self


    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None
            ) -> None:
        if self.session:
            await self.session.close()


    async def add_page_visit(self, normalized_url):
        """
        Add a page visit to the visited set in a thread-safe manner.
        
        Args:
            normalized_url (str): The normalized URL of the page being visited.
        """
        async with self.lock:
            if self.should_stop:
                return False

            if normalized_url in self.visited:
                return False

            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print(f"Reached maximum page limit of {self.max_pages}. Stopping crawl.")
                return False

            self.visited.add(normalized_url)
            return True



    async def get_html(self, url):
        """
        Fetch the HTML content of the given URL.
        
        Args:
            url (str): The URL to fetch.
        
        Returns:
            str: The HTML content of the page, or None if the request fails.
        """
        if self.session is None:
            return None

        try:
            async with self.session.get(url, headers={"User-Agent": "BootCrawler/1.0"}) as response: # Set a custom User-Agent to avoid potential blocking by some websites
                if response.status >= 400:
                    print(f"Request to {url} failed with status code {response.status}")
                    return None

                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    print(f"Request to {url} did not return HTML content (Content-Type: {content_type})")
                    return None

                return await response.text()

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None



    
    async def crawl_page(self, current_url=None) -> None:
        """
        Crawl a single page and extract its data, then recursively crawl its outgoing links.

        Args:
            current_url (str): The URL of the page to crawl. If None, the base URL will be used.
        """
        if self.should_stop:
            return

        if current_url is None:
            current_url = self.base_url

        current_url_obj = urlsplit(current_url)
        if current_url_obj.netloc != self.base_domain:
            return

        normalized_url = normalize_url(current_url)
        is_new = await self.add_page_visit(normalized_url)

        if not is_new:
            return

        # Get the current task and add it to the set of all tasks
        current_task = asyncio.current_task()
        if current_task is not None:
            self.all_tasks.add(current_task)

        try:
            async with self.semaphore:
                print(
                    f"Crawling {current_url} "
                    f"(Active: {self.max_concurrency - self.semaphore._value})"
                )

                html = await self.get_html(current_url)
                if html is None:
                    return

                page_info = extract_page_data(html, current_url)

                async with self.lock:
                    self.page_data[normalized_url] = page_info

                next_urls = page_info["outgoing_links"]

            # Don't proceed if the crawler has been stopped
            if self.should_stop:
                return

            tasks: list[asyncio.Task] = []

            for next_url in next_urls:
                if self.should_stop:
                    break

                task = asyncio.create_task(self.crawl_page(next_url))
                self.all_tasks.add(task)
                task.add_done_callback(self.all_tasks.discard)
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        finally:
            if current_task is not None:
                self.all_tasks.discard(current_task)


    async def crawl(self) -> dict[str, PageData]:
        """
        Start the crawling process from the base URL.
        
        Returns:
            dict: A dictionary containing the extracted data for all crawled pages.
        """
        await self.crawl_page(self.base_url)

        return self.page_data



async def crawl_site_async(base_url: str, max_concurrency: int, max_pages: int) -> dict[str, PageData]:
    """
    Crawl a website asynchronously starting from the base URL.
    
    Args:
        base_url (str): The base URL of the website to crawl.
    
    Returns:
        dict: A dictionary containing the extracted data for all crawled pages.
    """
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()
