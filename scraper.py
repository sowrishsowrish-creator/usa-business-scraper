'''
SowrishSithanathan
Data Scraper
June 8 2026
Scraper
'''

# selenium drives a real Chrome browser - it automates clicks/typing like a person
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import time
import random
import re
from urllib.parse import urlparse

# blocked domains list lives in its own file
from blockedURL import noURL


class BusinessScraper:

    def __init__(self):
        self.results = []
        self.driver = None
        # flag set when user chooses to stop mid-scrape
        self.stop_requested = False

        # generic page titles that arent actual business names
        # if the scraped h3 matches one of these, fall back to the domain name instead
        self.genericTitles = [
            "contact us", "contact", "contact us today", "about us", "about",
            "home", "homepage", "welcome", "menu", "our menu", "services",
            "our services", "gallery", "location", "locations", "hours",
            "reviews", "book now", "book online", "schedule", "schedule online"
        ]

        # directory / review sites to skip - the actual list lives in blockedURL.py
        self.blockedDomains = noURL


    def startBrowser(self):
        options = Options()

        # these options make Chrome harder for Google to flag as a bot
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)

        # hides the navigator.webdriver flag that sites check for
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )


    def closeBrowser(self):
        if (self.driver):
            self.driver.quit()
            self.driver = None


    def buildNameQuery(self, businessType, state):
        # query for finding a list of businesses - kept generic so it returns
        # listing pages instead of random "contact us" pages
        if (state == "USA"):
            urlSearch = f"{businessType} local small businesses in USA website"
        else:
            urlSearch = f"{businessType} local small businesses in {state} USA website"

        urlSearch = urlSearch.replace(" ", "+")
        return f"https://www.google.com/search?q={urlSearch}&num=10"


    def buildContactQuery(self, businessName, businessType, state):
        # query for ONE business's contact info
        if (state == "USA"):
            urlSearch = f"{businessName} {businessType} USA contact email phone website"
        else:
            urlSearch = f"{businessName} {businessType} {state} USA contact email phone website"

        urlSearch = urlSearch.replace(" ", "+")
        return f"https://www.google.com/search?q={urlSearch}&num=5"


    def extractEmail(self, text):
        pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        match = re.search(pattern, text)
        if (match):
            return match.group()
        return "N/A"


    def extractPhone(self, text):
        pattern = r"(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})"
        match = re.search(pattern, text)
        if (match):
            return match.group()
        return "N/A"


    def extractDomain(self, citeText):
        # cite text looks like "https://www.joesbakery.com › contact-us"
        # this pattern grabs just "joesbakery.com" out of it
        pattern = r"([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})"
        match = re.search(pattern, citeText)

        if (not match):
            return "N/A"

        domain = match.group(1)
        if (domain.startswith("www.")):
            domain = domain[4:]

        return domain


    def domainFromUrl(self, url):
        # more reliable than the cite text since it comes straight from the href
        if (not url):
            return "N/A"

        try:
            parsed = urlparse(url)
            domain = parsed.netloc
        except:
            return "N/A"

        if (domain.startswith("www.")):
            domain = domain[4:]

        if (not domain):
            return "N/A"

        return domain


    def nameFromDomain(self, domain):
        # turns "joes-bakery.com" into "Joes Bakery"
        if (domain == "N/A"):
            return "N/A"

        base = domain.split(".")[0]
        base = base.replace("-", " ").replace("_", " ")
        return base.title()


    def cleanBusinessName(self, name, domain):
        # if the title was generic (like "Contact Us"), use the domain instead
        cleanedName = name.strip()

        if (cleanedName.lower() in self.genericTitles):
            fallback = self.nameFromDomain(domain)
            if (fallback != "N/A"):
                return fallback

        return cleanedName


    def isBlockedDomain(self, domain):
        if (domain == "N/A"):
            return False

        for blocked in self.blockedDomains:
            if (domain == blocked or domain.endswith("." + blocked)):
                return True

        return False


    def getResultBlocks(self, statusCallback=None):
        # Google wraps each organic search result in a div.tF2Cxc
        try:
            return self.driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")
        except Exception as e:
            if (statusCallback):
                statusCallback(f"Could not find results: {e}")
            return []


    def getNameAndDomain(self, block):
        # business name is the h3 inside div.yuRUbf (the title link wrapper)
        # falls back to any h3 if that specific one isnt found
        try:
            nameEl = block.find_element(By.CSS_SELECTOR, "div.yuRUbf h3")
        except:
            try:
                nameEl = block.find_element(By.TAG_NAME, "h3")
            except:
                nameEl = None

        name = nameEl.text if nameEl else "N/A"

        # grab the real href off the title link - more reliable than the cite text
        try:
            linkEl = block.find_element(By.CSS_SELECTOR, "div.yuRUbf a")
            href = linkEl.get_attribute("href")
        except:
            href = None

        domain = self.domainFromUrl(href)

        if (domain == "N/A"):
            try:
                citeEl = block.find_element(By.TAG_NAME, "cite")
                citeText = citeEl.text
            except:
                citeText = "N/A"

            domain = self.extractDomain(citeText)

        name = self.cleanBusinessName(name, domain)

        return name, domain


    # ---- STEP 1: find business names ----

    def findBusinessNames(self, businessType, state, statusCallback=None):
        url = self.buildNameQuery(businessType, state)

        try:
            self.driver.get(url)
        except Exception as e:
            if (statusCallback):
                statusCallback(f"Browser error: {e}")
            return []

        time.sleep(random.uniform(2, 3))

        candidates = []
        seen_domains = set()

        page_num = 1
        while True:
            blocks = self.getResultBlocks(statusCallback)

            if (statusCallback):
                statusCallback(f"Found {len(blocks)} possible businesses on page {page_num} for {businessType} in {state}...")

            for block in blocks:
                try:
                    name, domain = self.getNameAndDomain(block)

                    if (name == "N/A" or name == ""):
                        continue

                    if (self.isBlockedDomain(domain)):
                        continue

                    if (domain in seen_domains):
                        continue

                    seen_domains.add(domain)
                    candidates.append((name, domain))

                except Exception:
                    continue

            # try to navigate to the next page of Google results
            try:
                next_btn = self.driver.find_element(By.ID, "pnnext")
            except Exception:
                next_btn = None

            if (not next_btn):
                break

            try:
                # small delay before clicking next
                time.sleep(random.uniform(1.5, 3))
                next_btn.click()
                page_num += 1
                time.sleep(random.uniform(2, 4))
            except Exception:
                break

        # small random delay so requests dont look automated
        time.sleep(random.uniform(2, 4))

        return candidates


    # ---- STEP 2: look up contact info for ONE business ----

    def findContactInfo(self, businessName, businessType, state, domain, statusCallback=None):
        url = self.buildContactQuery(businessName, businessType, state)

        try:
            self.driver.get(url)
        except Exception as e:
            if (statusCallback):
                statusCallback(f"Browser error: {e}")
            return "N/A", "N/A", domain

        time.sleep(random.uniform(2, 3))

        try:
            pageText = self.driver.find_element(By.TAG_NAME, "body").text
        except:
            pageText = ""

        email = self.extractEmail(pageText)
        phone = self.extractPhone(pageText)

        website = domain
        if (website == "N/A"):
            blocks = self.getResultBlocks(statusCallback)
            if (blocks):
                _, foundDomain = self.getNameAndDomain(blocks[0])
                website = foundDomain

        time.sleep(random.uniform(2, 4))

        return email, phone, website


    def scrapeOne(self, businessType, state, statusCallback=None):
        # step 1: find candidate businesses, step 2: look up each one's contact info
        candidates = self.findBusinessNames(businessType, state, statusCallback)

        if (not candidates):
            if (statusCallback):
                statusCallback(f"No businesses found for {businessType} in {state}.")
            return

        for i, (name, domain) in enumerate(candidates):

            if self.stop_requested:
                return

            if (statusCallback):
                statusCallback(f"Looking up contact info for {name} ({i + 1}/{len(candidates)})...")

            email, phone, website = self.findContactInfo(name, businessType, state, domain, statusCallback)

            record = {
                "Business Name" : name,
                "Business Type" : businessType,
                "Email" : email,
                "Phone" : phone,
                "State" : state,
                "Website" : website
            }

            self.results.append(record)

            # ask the user whether to continue when hitting checkpoints
            checkpoints = {50, 150, 250, 350}
            total = len(self.results)
            if total in checkpoints and statusCallback:
                try:
                    response = statusCallback({"confirm": True, "message": f"Reached {total} records. Continue looking for more?"})
                except Exception:
                    response = True

                # if the callback explicitly returned False, stop further scraping
                if response is False:
                    self.stop_requested = True
                    return


    def scrapeAll(self, businessTypes, states, statusCallback=None):
        if (statusCallback):
            statusCallback("Scraping Data from the Internet...")

        self.startBrowser()

        for state in states:
            for bType in businessTypes:
                if (statusCallback):
                    statusCallback(f"Scraping: {bType} in {state}...")
                self.scrapeOne(bType, state, statusCallback)

                # if user chose to stop during a checkpoint, break out
                if self.stop_requested:
                    if (statusCallback):
                        statusCallback("User stopped the scrape early.")
                    break
            if self.stop_requested:
                break

        self.closeBrowser()

        if (statusCallback):
            statusCallback(f"Browser closed. {len(self.results)} total records found.")