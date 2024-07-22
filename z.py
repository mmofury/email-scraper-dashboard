import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Fonction pour extraire les e-mails d'un contenu texte
def extract_emails(text):
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_regex, text)

# Fonction pour extraire les liens internes d'un footer
def extract_footer_links(url, soup):
    links = []
    footer = soup.find('footer')
    if footer:
        for a_tag in footer.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(url, href)
            # Ajouter uniquement les liens internes
            if urlparse(full_url).netloc == urlparse(url).netloc:
                links.append(full_url)
    return links

# Fonction principale pour scraper les e-mails d'un domaine à partir des liens du footer
def scrape_emails_from_footer_links(url):
    emails = set()
    visited = set()

    try:
        response = requests.get(url)
        print(f"Response status code: {response.status_code} for {url}")  # Debugging

        if response.status_code != 200:
            return emails

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraire les liens du footer
        footer_links = extract_footer_links(url, soup)
        print(f"Found {len(footer_links)} links in footer on {url}")  # Debugging

        # Visiter chaque lien trouvé dans le footer
        for link in footer_links:
            if link not in visited:
                visited.add(link)
                print(f"Visiting link from footer: {link}")  # Debugging
                try:
                    link_response = requests.get(link)
                    print(f"Response status code: {link_response.status_code} for {link}")  # Debugging

                    if link_response.status_code != 200:
                        continue

                    link_soup = BeautifulSoup(link_response.content, 'html.parser')
                    link_text = link_soup.get_text()
                    new_emails = extract_emails(link_text)
                    print(f"Found {len(new_emails)} new emails on {link}")  # Debugging
                    emails.update(new_emails)

                except Exception as e:
                    print(f"Erreur lors de la récupération de {link} : {e}")  # Debugging

    except Exception as e:
        print(f"Erreur lors de la récupération de {url} : {e}")  # Debugging

    return emails

# Exemple d'utilisation
domain_url = 'https://www.fightful.com/'
found_emails = scrape_emails_from_footer_links(domain_url)

print("Adresses e-mail trouvées :")
for email in found_emails:
    print(email)
