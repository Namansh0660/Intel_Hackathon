from flask import Flask, render_template, request
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time, json, re, csv

def scrape_google_maps(business, location):
    # Initialize the Selenium WebDriver
    service = Service(executable_path="chromedriver.exe")  # Adjust this if needed
    driver = webdriver.Chrome(service=service)

    # Open Google Maps
    driver.get('https://google.com/maps')

    # Search for the business and location
    search_query = f"{business} in {location}"
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(search_query + Keys.ENTER)

    # Allow some time for the page to load
    time.sleep(5)

    # Find the scrollable div
    scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')

    # Scroll within the element to load more results
    driver.execute_script("""
        var scrollableDiv = arguments[0];
        function scrollWithinElement(scrollableDiv) {
            return new Promise((resolve, reject) => {
                var totalHeight = 0;
                var distance = 1000;
                var scrollDelay = 3000;

                var timer = setInterval(() => {
                    var scrollHeightBefore = scrollableDiv.scrollHeight;
                    scrollableDiv.scrollBy(0, distance);
                    totalHeight += distance;

                    if (totalHeight >= scrollHeightBefore) {
                        totalHeight = 0;
                        setTimeout(() => {
                            var scrollHeightAfter = scrollableDiv.scrollHeight;
                            if (scrollHeightAfter > scrollHeightBefore) {
                                return;
                            } else {
                                clearInterval(timer);
                                resolve();
                            }
                        }, scrollDelay);
                    }
                }, 200);
            });
        }
        return scrollWithinElement(scrollableDiv);
    """, scrollable_div)

    # Extract items from the feed
    items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')

    results = []
    for item in items:
        data = {}

        try:
            data['title'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
        except Exception:
            pass

        try:
            data['link'] = item.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
        except Exception:
            pass

        try:
            data['website'] = item.find_element(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction] div > a').get_attribute('href')
        except Exception:
            pass

        try:
            rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
            rating_numbers = [float(piece.replace(",", ".")) for piece in rating_text.split(" ") if piece.replace(",", ".").replace(".", "", 1).isdigit()]

            if rating_numbers:
                data['stars'] = rating_numbers[0]
                data['reviews'] = int(rating_numbers[1]) if len(rating_numbers) > 1 else 0
        except Exception:
            pass

        try:
            text_content = item.text
            phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,3}))'
            matches = re.findall(phone_pattern, text_content)

            phone_numbers = [match[0] for match in matches]
            unique_phone_numbers = list(set(phone_numbers))

            data['phone'] = unique_phone_numbers[0] if unique_phone_numbers else None   
        except Exception:
            pass

        if data.get('title'):
            results.append(data)

    # Write the results to a CSV file
    csv_filename = f"{business}_{location}.csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['title', 'link', 'website', 'stars', 'reviews', 'phone'])
        writer.writeheader()
        writer.writerows(results)

    # Allow time for cleanup
    time.sleep(5)
    driver.quit()

    return csv_filename

app = Flask(__name__, template_folder="templates")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        # Get the business name and location from the form
        business = request.form['business']
        location = request.form['location']

        # For demonstration purposes, we are assuming the CSV file path is fixed
        csv_file = scrape_google_maps(business, location)  # Replace with the path to your CSV file

        # Read the CSV file using pandas
        try:
            data = pd.read_csv(csv_file)
        except Exception as e:
            return f"Error reading the CSV file: {e}"

        # Convert DataFrame to list of dictionaries
        csv_data = data.to_dict(orient='records')

        # Pass the business, location, and CSV data to the template
        return render_template('results.html', business=business, location=location, csv_data=csv_data)

if __name__ == '__main__':
    app.run(debug=True)
