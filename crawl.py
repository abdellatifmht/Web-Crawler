from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup, Tag

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


def get_urls_from_html(html, base_url):
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


def get_images_from_html(html, base_url):
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


def extract_page_data(html: str, page_url: str):
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
