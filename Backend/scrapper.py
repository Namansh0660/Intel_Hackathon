from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time, json, re, csv


service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)

driver.get('https://google.com/maps')

search = "Real estate in Chennai"
driver.find_element(By.NAME, "q").send_keys(search + Keys.ENTER)

# Allow some time for the page to load
time.sleep(5)

scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
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


items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')

results = []
for item in items:
    data = {}  # Declare data inside the loop to avoid overwriting previous iterations

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

    if data.get('title'):  # Only append if the title exists
        results.append(data)

# # Write the results to a JSON file
# with open('results.json', 'w', encoding='utf-8') as f:
#     json.dump(results, f, ensure_ascii=False, indent=2)

# Write the results to a CSV file
with open('results.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['title', 'link', 'website', 'stars', 'reviews', 'phone'])
    writer.writeheader()
    writer.writerows(results)

time.sleep(10)

driver.quit()
