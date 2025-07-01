from bs4 import BeautifulSoup

def extract_image_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    img = soup.find('img')
    if img and img.get('src'):
        return img['src']
    return None
