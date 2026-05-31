import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 10


@dataclass
class ScrapeResult:
    title: str = ""
    description: str = ""
    location: str = ""
    price: str = ""
    image_urls: list = field(default_factory=list)
    scrape_error: str | None = None


def _meta_content(soup, property_name):
    tag = soup.find("meta", property=property_name) or soup.find(
        "meta", attrs={"name": property_name}
    )
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def _parse_price(text):
    if not text:
        return ""
    match = re.search(r"[\d,.]+", text.replace(",", ""))
    if match:
        return match.group(0)
    return text.strip()


def scrape_facebook_listing(url):
    result = ScrapeResult()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or "facebook.com" not in parsed.netloc:
        result.scrape_error = "Please enter a valid Facebook Marketplace URL."
        return result

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-GB,en;q=0.9"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        result.scrape_error = (
            f"Could not fetch the listing ({exc}). "
            "Use the manual form below to enter product details."
        )
        return result

    soup = BeautifulSoup(response.text, "html.parser")

    result.title = _meta_content(soup, "og:title") or _meta_content(soup, "twitter:title")
    result.description = _meta_content(soup, "og:description") or _meta_content(
        soup, "description"
    )

    og_image = _meta_content(soup, "og:image")
    if og_image:
        result.image_urls.append(og_image)

    for img in soup.select("img[src]")[:10]:
        src = img.get("src", "")
        if src.startswith("http") and src not in result.image_urls:
            result.image_urls.append(src)
        if len(result.image_urls) >= 8:
            break

    page_text = soup.get_text(" ", strip=True)
    price_match = re.search(r"£\s*[\d,.]+", page_text)
    if price_match:
        result.price = _parse_price(price_match.group(0))
    else:
        result.price = _parse_price(result.title)

    location_match = re.search(
        r"(London|Manchester|Birmingham|Leeds|Glasgow|Liverpool|Bristol|UK|Kenya|Nairobi)",
        page_text,
        re.I,
    )
    if location_match:
        result.location = location_match.group(0)

    if not result.title and not result.description:
        result.scrape_error = (
            "Facebook blocked or hid listing content. "
            "Enter product details manually below."
        )

    return result


def scrape_price_as_decimal(price_str):
    if not price_str:
        return None
    try:
        return Decimal(price_str.replace(",", ""))
    except InvalidOperation:
        return None
