import requests
import pandas as pd
from bs4 import BeautifulSoup


class TheWhiteHouseScraper:

    def __init__(self, url):
        """
        Initialize TheWhiteHouseScraper with the given URL and user agent headers.
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        self.url = url

    def get_html_content(self):
        '''
        Function to fetch the HTML content using requests and parse it using BeautifulSoup.
        '''
        response = requests.get(self.url, headers=self.headers)

        if response.status_code == 200:
            html_content = response.text
            # Use BeautifulSoup to parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
        else:
            raise Exception(f"Failed to fetch the page. Status code: {response.status_code}")

    def get_page_num(self, soup):
        """
        Get the page number from the given BeautifulSoup object.
        """
        page_number = soup.find_all('a', class_='page-numbers')[-1].text
        return int(page_number.replace('Page ', ''))

    def get_articles(self, soup, category):
        """
        Extract information from articles on the page using Beautiful Soup.
        """
        temp_list = []
        articles = soup.find_all('article')
        for article in articles:
            a_title = article.find('a', class_='news-item__title').text.strip()
            a_link = article.find('a', class_='news-item__title')['href']
            a_date = article.find('time', class_='posted-on entry-date published updated')['datetime']
            a_category = article.find('a', rel='category tag').text

            # Fetch content from the a_link
            self.url = a_link
            article_soup = self.get_html_content()

            # Extract the section with class 'body-content'
            body_content_section = article_soup.find('section', class_='body-content')

            if category == 'speeches-remarks' or category == 'press-briefings':
                try:
                    # Extract all p elements with class 'has-text-align-center'
                    location_elements = body_content_section.find_all('p', class_='has-text-align-center')

                    # Extract the text from location elements and join them with '; '
                    a_location = '; '.join(
                        [location.get_text(separator='; ').strip() for location in location_elements])

                    # Remove the location elements from the list of all p elements
                    other_p_elements = [p for p in body_content_section.find_all('p') if p not in location_elements]

                    # Extract the text from the remaining p elements and join them with a new line
                    a_text = '\n\n'.join([p.get_text(separator='\n').strip() for p in other_p_elements])

                except IndexError:
                    # Handle the case where the content is in tables
                    a_location = article_soup.find_all('table')[0].get_text(separator='; ')
                    a_text = article_soup.find_all('table')[1].get_text(separator='\n')
            elif category == 'statements-releases':
                a_location = None
                a_text = body_content_section.get_text(separator='\n').strip()
            else:
                raise Exception('The category does not exist.')

            temp_list.append({'Title': a_title, 'Date': a_date,
                              'Category': a_category, 'Location': a_location,
                              'Text': a_text})

        return temp_list
