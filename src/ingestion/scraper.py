import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
from urllib.parse import unquote
import logging

logger = logging.getLogger("ingestion")

# Target HDFC Mutual Fund Growth schemes from Groww
FUND_URLS = [
    "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-short-term-opportunities-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-nifty-50-index-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
]


class GrowwScraper:
    def __init__(self):
        self.results = []

    def _clean_text(self, text):
        """Strip whitespace and non-breaking spaces."""
        if not text:
            return None
        return text.strip().replace('\xa0', ' ').replace('\u200b', '')

    def _extract_text_after_label(self, text, label):
        """Find a label in the text and return the next non-empty line after it."""
        idx = text.find(label)
        if idx == -1:
            return None
        after = text[idx + len(label):]
        lines = after.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped and stripped != label:
                return stripped
        return None

    def _extract_nav(self, text):
        """Extract NAV value and date from the metrics block."""
        nav_value = None
        nav_date = None

        # Groww renders NAV as: "NAV: 17 Apr '26" followed by "₹27.06"
        # Pattern 1: DD Mon 'YY  (e.g. 17 Apr '26)
        date_match = re.search(
            r"NAV:\s*(\d{1,2}\s+[A-Za-z]{3}\s+'\d{2})", text
        )
        if date_match:
            nav_date = self._clean_text(date_match.group(1))
        else:
            # Fallback: grab anything after "NAV:" up to the newline
            fb = re.search(r'NAV:\s*(.+)', text)
            if fb:
                nav_date = self._clean_text(fb.group(1))

        # NAV value: first ₹ amount after the "NAV:" block
        idx = text.find('NAV:')
        if idx != -1:
            after = text[idx:]
            rupee_match = re.search(r'₹([\d,]+\.?\d*)', after)
            if rupee_match:
                nav_value = rupee_match.group(1).replace(',', '')

        logger.debug(f"  NAV extracted -> value={nav_value!r}, date={nav_date!r}")
        return nav_value, nav_date


    def _extract_rupee_value(self, text, label):
        """Extract a rupee value after a given label."""
        idx = text.find(label)
        if idx == -1:
            return None
        after = text[idx:]
        match = re.search(r'₹([\d,]+\.?\d*)', after[:300])
        if match:
            return match.group(1).replace(',', '')
        return None

    def _extract_percentage(self, text, label):
        """Extract a percentage value after a given label."""
        idx = text.find(label)
        if idx == -1:
            return None
        after = text[idx + len(label):]
        match = re.search(r'([\d.]+)%', after[:200])
        if match:
            return match.group(1)
        return None

    def _extract_rating(self, text):
        """Extract the Groww rating (a single digit after 'Rating')."""
        # Find "Rating" in the metrics block (before Return calculator)
        idx = text.find('Rating')
        if idx == -1:
            return None
        # Make sure this is the metrics Rating, not a definition
        after = text[idx + len('Rating'):]
        match = re.search(r'^[\s\n]*(\d)', after)
        if match:
            return match.group(1)
        return None

    def _extract_category_subcategory_risk(self, text):
        """Extract category, sub-category and risk from filter link patterns."""
        category = None
        sub_category = None
        risk_label = None

        cat_match = re.search(r'\[([^\]]+)\]\(/mutual-funds/filter\?cat=', text)
        if cat_match:
            category = cat_match.group(1)

        sub_match = re.search(r'\[([^\]]+)\]\(/mutual-funds/filter\?sub_cat=', text)
        if sub_match:
            sub_category = sub_match.group(1)

        risk_match = re.search(r'\[([^\]]+)\]\(/mutual-funds/filter\?risk=', text)
        if risk_match:
            risk_label = risk_match.group(1)

        return category, sub_category, risk_label

    def _extract_exit_load(self, text):
        """Extract exit load description."""
        match = re.search(r'(?:### Exit Load|#### Exit load)\s*\n+.*?\n*(Exit load of [^\n]+)', text)
        if match:
            return self._clean_text(match.group(1))
        # Fallback: look for "Exit load of" anywhere
        match2 = re.search(r'(Exit load of [^\n]+)', text)
        if match2:
            return self._clean_text(match2.group(1))
        # Check for "Nil" exit load
        idx = text.find('Exit Load')
        if idx != -1:
            after = text[idx:idx + 300]
            if 'Nil' in after or 'nil' in after:
                return 'Nil'
        return None

    def _extract_benchmark(self, text):
        """Extract fund benchmark. Pattern: 'Fund benchmark<value>' (no separator)."""
        match = re.search(r'Fund benchmark\s*[:\s]*([A-Z][^\n]+)', text)
        if match:
            val = self._clean_text(match.group(1))
            # Clean up trailing link artifacts
            if val and '[' in val:
                val = val[:val.index('[')].strip()
            return val
        return None

    def _extract_fund_manager(self, text):
        """Extract the first/primary fund manager name."""
        idx = text.find('Fund management')
        if idx == -1:
            return None
        after = text[idx:idx + 500]
        # Pattern: "### XX Full Name Month Year - Present"
        match = re.search(r'###\s+[A-Z]{2}\s+(.+?)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', after)
        if match:
            return self._clean_text(match.group(1))
        return None

    def _extract_launch_date(self, text):
        """Extract launch date from Fund house section."""
        match = re.search(r'Launch Date\s*[:\s]*(\d{1,2}\s+\w+\s+\d{4})', text)
        if match:
            return self._clean_text(match.group(1))
        return None

    def _extract_plan_type(self, url, scheme_name):
        """Derive plan type from URL/scheme name."""
        if 'direct' in url.lower() or 'Direct' in scheme_name:
            return 'Direct'
        return 'Regular'

    def _clean_scheme_name(self, title):
        """Strip the Groww page title suffix."""
        if not title:
            return "Unknown Scheme"
        name = title.split('|')[0].strip()
        # Remove "- NAV, Mutual Fund Performance & Portfolio" suffix
        name = re.sub(r'\s*-\s*NAV.*$', '', name).strip()
        return name

    def _build_content_summary(self, scheme_name, sd):
        """Build a clean, dense prose summary from structured data for embedding."""
        parts = []

        # Line 1: Identity
        cat = sd.get('category') or 'Unknown'
        sub = sd.get('sub_category') or 'Unknown'
        risk = sd.get('risk_label') or 'Unknown'
        plan = sd.get('plan_type') or 'Direct'
        parts.append(
            f"{scheme_name} is a {cat} mutual fund in the {sub} sub-category, "
            f"classified as {risk} risk. It is a {plan} plan."
        )

        # Line 2: Key metrics
        metrics = []
        if sd.get('nav_value') and sd.get('nav_date'):
            metrics.append(f"The current NAV is ₹{sd['nav_value']} as of {sd['nav_date']}.")
        if sd.get('fund_size_aum'):
            metrics.append(f"The fund has an AUM of ₹{sd['fund_size_aum']} Cr.")
        if sd.get('expense_ratio'):
            metrics.append(f"The expense ratio is {sd['expense_ratio']}% per annum.")
        if sd.get('rating'):
            metrics.append(f"The Groww rating is {sd['rating']} out of 5.")
        if metrics:
            parts.append("Key Metrics: " + " ".join(metrics))

        # Line 3: Investment requirements
        inv = []
        if sd.get('min_sip'):
            inv.append(f"The minimum SIP amount is ₹{sd['min_sip']}.")
        if sd.get('min_lumpsum'):
            inv.append(f"The minimum lumpsum investment is ₹{sd['min_lumpsum']}.")
        if sd.get('exit_load'):
            inv.append(f"Exit load: {sd['exit_load']}.")
        if inv:
            parts.append("Investment Details: " + " ".join(inv))

        # Line 4: Fund profile
        profile = []
        if sd.get('benchmark'):
            profile.append(f"The fund benchmark is {sd['benchmark']}.")
        if sd.get('fund_manager'):
            profile.append(f"The fund is managed by {sd['fund_manager']}.")
        if sd.get('launch_date'):
            profile.append(f"Launch date: {sd['launch_date']}.")
        if sd.get('isin'):
            profile.append(f"ISIN: {sd['isin']}.")
        if profile:
            parts.append("Fund Profile: " + " ".join(profile))

        return "\n\n".join(parts)

    async def scrape_fund(self, context, url):
        page = await context.new_page()
        logger.info(f"Scraping: {url}")
        try:
            # Wait for network to be mostly idle so JS-rendered NAV data loads
            await page.goto(url, wait_until="networkidle", timeout=90000)

            # Explicitly wait for the NAV section to appear in the DOM
            try:
                await page.wait_for_selector(
                    "text=NAV", timeout=15000
                )
            except Exception:
                logger.warning(f"  NAV element did not appear within 15 s for {url} — page may be incomplete")

            # Small safety buffer for React hydration to finish
            await asyncio.sleep(3)

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            title = soup.title.string if soup.title else "Unknown Scheme"
            scheme_name = self._clean_scheme_name(title)

            # Convert main content to markdown for regex-based extraction
            from markdownify import markdownify as md
            main_content = soup.find('main') or soup.find('body')
            markdown_text = md(str(main_content), heading_style="ATX")

            # --- Targeted Extraction ---
            category, sub_category, risk_label = self._extract_category_subcategory_risk(markdown_text)
            nav_value, nav_date = self._extract_nav(markdown_text)
            min_sip = self._extract_rupee_value(markdown_text, 'Min. for SIP')
            min_lumpsum = self._extract_rupee_value(markdown_text, 'Min. for 1st investment')
            fund_size = self._extract_rupee_value(markdown_text, 'Fund size (AUM)')
            expense_ratio = self._extract_percentage(markdown_text, 'Expense ratio')
            rating = self._extract_rating(markdown_text)
            exit_load = self._extract_exit_load(markdown_text)
            benchmark = self._extract_benchmark(markdown_text)
            fund_manager = self._extract_fund_manager(markdown_text)
            launch_date = self._extract_launch_date(markdown_text)
            plan_type = self._extract_plan_type(url, scheme_name)

            structured_data = {
                "nav_value": nav_value,
                "nav_date": nav_date,
                "min_sip": min_sip,
                "min_lumpsum": min_lumpsum,
                "fund_size_aum": fund_size,
                "expense_ratio": expense_ratio,
                "rating": rating,
                "risk_label": risk_label,
                "category": category,
                "sub_category": sub_category,
                "plan_type": plan_type,
                "benchmark": benchmark,
                "exit_load": exit_load,
                "fund_manager": fund_manager,
                "launch_date": launch_date,
                "isin": None  # Not available on Groww pages
            }

            # Count extracted fields
            extracted = sum(1 for v in structured_data.values() if v is not None)
            total = len(structured_data)
            logger.info(f"  -> {scheme_name}: Extracted {extracted}/{total} fields")
            if extracted < 8:
                logger.warning(f"  Low extraction count for {url}")

            content_summary = self._build_content_summary(scheme_name, structured_data)

            today = datetime.now().strftime("%Y-%m-%d")

            return {
                "url": url,
                "scheme_name": scheme_name,
                "timestamp": today,
                "structured_data": structured_data,
                "content": content_summary
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}", exc_info=True)
            return None
        finally:
            await page.close()

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            tasks = [self.scrape_fund(context, url) for url in FUND_URLS]
            self.results = [r for r in await asyncio.gather(*tasks) if r]
            await browser.close()
        return self.results


if __name__ == "__main__":
    scraper = GrowwScraper()
    final_data = asyncio.run(scraper.run())

    os.makedirs('data', exist_ok=True)
    with open('data/raw_scraped_data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)
    logger.info(f"Successfully scraped {len(final_data)} schemes.")

    # Print summary
    for entry in final_data:
        sd = entry["structured_data"]
        print(f"\n{entry['scheme_name']}:")
        for k, v in sd.items():
            print(f"  {k}: {v}")
