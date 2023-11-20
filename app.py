from flask import Flask, request, jsonify, send_from_directory
import csv
import time
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse

app = Flask(__name__, static_folder="public")

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    def extract_links_from_page(driver):
        anchors = driver.find_elements(By.CSS_SELECTOR, '.app-aware-link')
        return [anchor.get_attribute('href') for anchor in anchors]

    data = request.json
    email = data.get('email', 'example@gmail.com')
    password = data.get('password', 'PasswordToLogin')
    search = data.get('search', 'talent')
    college = data.get('college', 'symbiosis')
    max_pages = int(data.get('pages', 100))

    # Encoding the strings
    search = urllib.parse.quote(search)
    college = urllib.parse.quote(college)

    
    badUrls = [
        "https://www.linkedin.com/feed/?nis=true",
        "https://www.linkedin.com/feed/?nis=true&",
        "https://www.linkedin.com/mynetwork/?",
        "https://www.linkedin.com/jobs/?",
        "https://www.linkedin.com/messaging/?",
        "https://www.linkedin.com/notifications/?"
    ]

    def login_and_scrape():
        

        options = webdriver.ChromeOptions()
        options.headless = False
        driver = webdriver.Chrome(options=options)

        driver.get('https://www.linkedin.com/login')

        # Login process
        driver.find_element(By.ID, 'username').send_keys(email)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.CLASS_NAME, 'btn__primary--large').click()
        
        # time.sleep(5)  # Wait for login to complete
        WebDriverWait(driver, 500).until(EC.presence_of_element_located((By.CLASS_NAME, 'feed-identity-module__actor-meta')))

        urls = []

        for i in range(1, max_pages + 1):
            searchURL = f"https://www.linkedin.com/search/results/people/?geoUrn=%5B%22102713980%22%5D&keywords={search}&origin=FACETED_SEARCH&schoolFreetext=%22{college}%22&sid=G6*&page={i}"
            driver.get(searchURL)
            
            print(f"Navigated to search page with keywords: {search} and {college} - Page: {i}")

            time.sleep(5)  # Sleep for 5 seconds

            newUrls = extract_links_from_page(driver)
            urls.extend([url for url in newUrls if url not in badUrls and "https://www.linkedin.com/search/results/people/" not in url])

        def extract_details(driver, url):
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.pv-text-details__about-this-profile-entrypoint')))
            time.sleep(2)  # Sleep for stability, adjust as needed

            # Extract the name
            name_element = driver.find_element(By.CSS_SELECTOR, '.pv-text-details__about-this-profile-entrypoint h1')
            name = name_element.text if name_element else 'Name not found'

            # Extract the text content
            text_content_element = driver.find_element(By.CSS_SELECTOR, '.inline-show-more-text')
            text_content = text_content_element.text if text_content_element else 'Text content not found'

            return name, text_content   

        # Making URLS unique
        urls = list(set(urls))

        # with open("output.txt", "w") as file:
        #     for item in urls:
        #         file.write(item + "\n")

        # Save the URLs to a CSV file
        with open('links.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for link in urls:
                name, text_content = extract_details(driver, link)
                writer.writerow([link, name, text_content])

        print('URLs saved to links.csv.')

        driver.quit()  # Close the browser window
        return jsonify({"message": "Links.csv generated", "success": True})

    return login_and_scrape()
    

@app.route('/download')
def download():
    return send_from_directory('.', 'links.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=3000)

