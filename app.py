from flask import Flask, request, jsonify, send_from_directory
import csv
import time
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


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
    search = search.replace(" ", "%20")
    college = college.replace(" ", "%20")
    max_pages = int(data.get('pages', 100))
    
    # Encode keywords
    encodedKeyword1 = search.replace(' ', '%20')
    encodedKeyword2 = college.replace(' ', '%20')
    
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
        
        time.sleep(2)  # Wait for login to complete

        urls = []

        for i in range(1, max_pages + 1):
            searchURL = f"https://www.linkedin.com/search/results/people/?geoUrn=%5B%22102713980%22%5D&keywords={search}&origin=FACETED_SEARCH&schoolFreetext=%22{college}%22&sid=G6*&page={i}"
            driver.get(searchURL)
            
            print(f"Navigated to search page with keywords: {search} and {college} - Page: {i}")

            time.sleep(5)  # Sleep for 5 seconds

            newUrls = extract_links_from_page(driver)
            urls.extend([url for url in newUrls if url not in badUrls])

        # Save the URLs to a CSV file
        with open('links.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for link in urls:
                writer.writerow([link])

        print('URLs saved to links.csv.')

        driver.quit()  # Close the browser window
        return jsonify({"message": "Links.csv generated", "success": True})

    return login_and_scrape()
    

@app.route('/download')
def download():
    return send_from_directory('.', 'links.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=3000)
