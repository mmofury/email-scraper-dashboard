import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import csv
from io import StringIO, BytesIO
import json
import pandas as pd

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
            if urlparse(full_url).netloc == urlparse(url).netloc:
                links.append(full_url)
    else:
        common_footer_containers = ['div', 'section', 'nav']
        for container in common_footer_containers:
            container_tags = soup.find_all(container, class_=re.compile(r"footer|Footer|FOOTER"))
            for tag in container_tags:
                for a_tag in tag.find_all('a', href=True):
                    href = a_tag['href']
                    full_url = urljoin(url, href)
                    if urlparse(full_url).netloc == urlparse(url).netloc:
                        links.append(full_url)
    return links

# Fonction pour filtrer les e-mails par domaine
def filter_emails_by_domain(emails, allowed_domains):
    filtered_emails = []
    for email in emails:
        domain = email.split('@')[1]
        if domain not in allowed_domains:
            filtered_emails.append(email)
    return filtered_emails

# Fonction pour valider et compléter l'URL
def validate_and_complete_url(url):
    if not urlparse(url).scheme:
        return 'https://' + url
    return url

# Fonction principale pour scraper les e-mails d'un domaine à partir des liens du footer
def scrape_emails_from_footer_links(url):
    emails = set()
    visited = set()
    url = validate_and_complete_url(url)

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return emails

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraire les liens du footer
        footer_links = extract_footer_links(url, soup)

        # Visiter chaque lien trouvé dans le footer
        for link in footer_links:
            if link not in visited:
                visited.add(link)
                try:
                    link_response = requests.get(link)
                    if link_response.status_code != 200:
                        continue

                    link_soup = BeautifulSoup(link_response.content, 'html.parser')
                    link_text = link_soup.get_text()
                    new_emails = extract_emails(link_text)
                    emails.update(new_emails)

                except Exception as e:
                    print(f"Erreur lors de la récupération de {link} : {e}")

    except Exception as e:
        print(f"Erreur lors de la récupération de {url} : {e}")

    return emails

# Configuration de l'application Streamlit
st.title('Bulk Email Scraper and Dashboard')

# Formulaire pour entrer les domaines
domains = st.text_area('Enter domains (one per line):')

# Bouton pour scraper les e-mails
if st.button('Scrape Emails'):
    domain_list = domains.split()
    results = {}
    for domain in domain_list:
        emails = scrape_emails_from_footer_links(domain)
        filtered_emails = filter_emails_by_domain(emails, {'gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'comcast.net', 'cogeco.ca'})
        results[domain] = list(filtered_emails)
    
    # Afficher les résultats
    if results:
        st.write('### Results:')
        for domain, emails in results.items():
            st.write(f"**{domain}**: {', '.join(emails)}")
        
        # Convertir les résultats en CSV
        csv_data = StringIO()
        cw = csv.writer(csv_data)
        cw.writerow(['Domain', 'Emails'])
        for domain, emails in results.items():
            row = [domain] + emails
            cw.writerow(row)
        
        st.download_button(
            label="Download CSV",
            data=csv_data.getvalue(),
            file_name='email_results.csv',
            mime='text/csv'
        )

# Section Dashboard
st.write('## Dashboard')

# Téléchargement du fichier CSV
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Data from the uploaded file")
    st.dataframe(df)

    # Ajouter une nouvelle entrée
    st.write("### Add a new entry")
    with st.form("add_entry"):
        domain = st.text_input('Domain')
        contact_date = st.date_input('Contact Date')
        notes = st.text_area('Notes')
        submitted = st.form_submit_button("Add Entry")
        if submitted:
            new_entry = pd.DataFrame([[domain, contact_date, notes]], columns=["Domain", "Contact Date", "Notes"])
            df = pd.concat([df, new_entry], ignore_index=True)
            st.write("### Updated Data")
            st.dataframe(df)

            # Convertir le DataFrame en CSV
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Updated CSV",
                data=csv_data,
                file_name='updated_dashboard.csv',
                mime='text/csv'
            )
