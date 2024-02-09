import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException


class TheWhiteHouseScraper:

    def __init__(self, url):
        """
        Initialize TheWhiteHouseScraper with the given URL and user agent headers.

        Args:
            url (str): The URL of the website to scrape.
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        self.url = url

    def get_html_content(self):
        """
        Function to fetch the HTML content using requests and parse it using BeautifulSoup.

        Returns:
            soup (BeautifulSoup): Parsed HTML content.
        """
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

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            int: The page number.
        """
        page_number = soup.find_all('a', class_='page-numbers')[-1].text
        return int(page_number.replace('Page ', ''))

    def get_articles(self, soup, category):
        """
        Extract information from articles on the page using Beautiful Soup.

        Args:
            soup (BeautifulSoup): Parsed HTML content.
            category (str): The category of articles to extract.

        Returns:
            list: List of dictionaries containing article details.
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


class TheEuropeanCommissionScraper:
    def __init__(self, geko_path=None, url=None, profile_path=None):
        """
        Constructor for the class.

        Args:
            geko_path (str): Path to the Gecko driver executable.
            url (str): URL to scrape. If None, defaults to the European Commission press corner homepage.
            profile_path (str): Path to the Firefox profile to be used is there is one.
        """
        self.geko_path = geko_path
        self.profile_path = profile_path
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}
        if url:
            self.url = url
        else:
            self.url = 'https://ec.europa.eu/commission/presscorner/home/en'

    def start_up(self, link, geko_path, profile_path=None, browser=None):
        """
        Function to set up the browser and open the selected link.

        Args:
            link (str): The URL to open.
            geko_path (str): Path to the Gecko driver executable.
            profile_path (str): Path to the Firefox profile to be used if there is any.
            browser: Optional existing webdriver instance.

        Returns:
            browser: The initialized webdriver instance.
        """
        if not browser:
            if profile_path:
                firefox_options = webdriver.FirefoxOptions()
                firefox_options.add_argument(f'--profile={profile_path}')
                service = Service(geko_path)
                browser = webdriver.Firefox(service=service, options=firefox_options)
            else:
                profile = webdriver.FirefoxProfile()
                options = Options()
                options.profile = profile
                service = Service(geko_path)
                browser = webdriver.Firefox(service=service, options=options)

        browser.get(link)
        time.sleep(2)
        return browser

    def fill_in_filters(self, browser, document_type=None):
        """
        Fill in filters on the European Commission press corner website.

        Args:
            browser: The initialized webdriver instance.
            document_type (str): Optional CSS selector for selecting document types.

        Returns:
            browser: The updated webdriver instance.
        """
        # Click on 'More criteria'
        browser.find_element(by='xpath', value='//a[@class="ecl-link ecl-link--icon"]').click()

        # Click on the Commissioner box
        browser.find_elements(by='xpath', value='//div[@class="ecl-select__container ecl-select__container--m"]')[
            1].click()

        # Select and search the Commissioner
        css = 'form.ng-dirty > div:nth-child(5) > div:nth-child(3) > div:nth-child(3) > div:nth-child(2) > div:nth-child(3) > div:nth-child(1)'
        browser.find_element('css selector', css).click()

        css = 'form.ng-valid > div:nth-child(5) > div:nth-child(3) > div:nth-child(3) > div:nth-child(2) > div:nth-child(4) > button:nth-child(2)'
        browser.find_element('css selector', css).click()

        # Select Document Type
        if document_type:
            browser.find_element('css selector', document_type).click()

        # Click on Search
        css = 'div.ecl-form-group:nth-child(6) > div:nth-child(2) > div:nth-child(1) > button:nth-child(1)'
        browser.find_element('css selector', css).click()
        time.sleep(2)

        return browser

    def get_articles(self, browser):
        """
        Scrape articles from the European Commission press corner website.

        Args:
            browser: The initialized webdriver instance.

        Returns:
            browser: The updated webdriver instance.
            temp_list (list): List of dictionaries containing article details.
        """
        temp_list = []

        # Get articles
        articles = browser.find_elements(by='xpath', value='//a[@class="ecl-link ecl-list-item__link"]')
        for article in articles:
            a_title = article.find_element('xpath',
                                           './/h3[@class="ecl-list-item__title ecl-heading ecl-heading--h3"]').text
            a_link = article.get_attribute('href')
            a_date = article.find_elements('xpath', './/span[@class="ecl-meta__item"]')[1].text
            a_category = article.find_elements('xpath', './/span[@class="ecl-meta__item"]')[0].text

            # Open a new window
            browser.execute_script("window.open('')")

            # Switch to the new window and open the article URL
            browser.switch_to.window(browser.window_handles[1])
            browser.get(a_link)
            time.sleep(2)

            a_text = browser.find_element('xpath', '//div[@class="ecl-paragraph-detail"]').text

            temp_list.append({'Title': a_title, 'Date': a_date,
                              'Category': a_category, 'Text': a_text})

            # Close the current page
            browser.close()

            # Switch back to the main page
            browser.switch_to.window(browser.window_handles[0])

        return browser, temp_list

    def element_exists(self, browser, path, e_type):
        """
        Check if an element exists on the current webpage.

        Args:
            browser: The initialized webdriver instance.
            path (str): Path to the element.
            e_type (str): Type of the element (xpath, id, css, class, link).

        Returns:
            bool: True if the element exists, False otherwise.
        """
        try:
            if e_type == "xpath":
                browser.find_element('xpath', path)
            elif e_type == "id":
                browser.find_element('id', path)
            elif e_type == "css":
                browser.find_element('css selector', path)
            elif e_type == "class":
                browser.find_element('class name', path)
            elif e_type == "link":
                browser.find_element('link text', path)
        except NoSuchElementException:
            return False
        return True
