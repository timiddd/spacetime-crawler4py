import re
import hashlib
import nltk
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser
from collections import defaultdict

nltk.download('punkt')

# Global tracking variables
Visited = set()
Unique_Urls = set()
Common_Words = defaultdict(int)
Longest_Page = ('', 0)
Subdomain = defaultdict(int)
Stop_Words = set([
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but',
    'by', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
    'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'me', 'more',
    'most', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other',
    'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such',
    'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they',
    'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were',
    'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with', 'would', 'you', 'your',
    'yours', 'yourself', 'yourselves'])


def scraper(url, resp):
    clean_url, _ = urldefrag(url)
    Unique_Urls.add(clean_url)

    if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
        save_progress()
        return []

    links = extract_next_links(url, resp)
    valid_links = [link for link in links if is_valid(link)]

    text_tokens = tokenize_response(resp)
    if text_tokens:
        count_words(text_tokens)
        update_longest_page(url, text_tokens)
        update_subdomains(url)

    save_progress()

    return valid_links


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    links = []

    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            absolute_link = urljoin(url, href)
            clean_link, _ = urldefrag(absolute_link)
            links.append(clean_link)

    except Exception as e:
        print(f"Error extracting links from {url}: {e}")

    return links
    # return list()


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return False

        domain = parsed.netloc.lower()
        if not (domain.endswith("ics.uci.edu") or domain.endswith("cs.uci.edu") or domain.endswith(
                "informatics.uci.edu") or domain.endswith("stat.uci.edu") or (domain.endswith(
                "today.uci.edu") and "/department/information_computer_sciences" in parsed.path)):
            return False

        if re.search(
                r"\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4"
                r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                r"|epub|dll|cnf|tgz|sha1"
                r"|thmx|mso|arff|rtf|jar|csv"
                r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False

        return True

    except Exception as e:
        print(f"Error in is_valid for URL {url}: {e}")
        return False


def tokenize_response(resp):
    # print("!")
    try:

        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        tokens = nltk.tokenize.word_tokenize(soup.get_text())
        # print(len(tokens))
        return [token.lower() for token in tokens if token.isalpha()]
    except:

        return []


def count_words(tokens):
    for token in tokens:
        if token not in Stop_Words and len(token) > 1:
            Common_Words[token] += 1


def update_longest_page(url, tokens):
    global Longest_Page
    if len(tokens) > Longest_Page[1]:
        Longest_Page = (url, len(tokens))


def update_subdomains(url):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.endswith("uci.edu"):
        Subdomain[domain] += 1


def save_progress():
    with open("unique_urls.txt", "w") as f:
        f.write(f"Total unique pages: {len(Unique_Urls)}\n")

    with open("longest_page.txt", "w") as f:
        f.write(f"Longest page: {Longest_Page[0]} ({Longest_Page[1]} words)\n")

    with open("subdomains.txt", "w") as f:
        for subdomain, count in sorted(Subdomain.items()):
            f.write(f"{subdomain}, {count}\n")

    with open("common_words.txt", "w") as f:
        for word, freq in sorted(Common_Words.items(), key=lambda x: x[1], reverse=True)[:50]:
            f.write(f"{word}: {freq}\n")
