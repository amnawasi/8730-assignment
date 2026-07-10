import os
import requests
from bs4 import BeautifulSoup

url = "https://smartcentres.com/investing/"

response = requests.get(url)
soup = BeautifulSoup(response.text, "lxml")

folder = "data/raw/smartcentres"
os.makedirs(folder, exist_ok=True)

pdf_links = []

for link in soup.find_all("a"):
    href = link.get("href")
    if href and href.endswith(".pdf"):
        pdf_links.append(href)

print(f"Found {len(pdf_links)} PDF files")

for pdf_url in pdf_links:
    filename = pdf_url.split("/")[-1]

    print("Downloading:", filename)

    pdf = requests.get(pdf_url)

    with open(os.path.join(folder, filename), "wb") as f:
        f.write(pdf.content)

print("\nFinished!")