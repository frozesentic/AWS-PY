import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time

def setup_logger():
    logging.basicConfig(
        format='[%(asctime)s] [%(levelname)s]: %(message)s',
        level=logging.INFO,
        handlers=[logging.StreamHandler()]
    )

def scrape_amazon():
    setup_logger()
    search_term = "laptop"  # Replace with the item you want to search for
    base_url = f"https://www.amazon.nl/s?k={search_term}"

    # Configure the path to your downloaded web driver
    driver_path = r"C:\Users\{User}\PycharmProjects\WS&PC\chromedriver.exe"
    service = webdriver.chrome.service.Service(driver_path)
    service.start()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (without GUI)
    options.add_argument("--disable-gpu")  # Disable GPU acceleration

    driver = webdriver.Chrome(service=service, options=options)

    # Keep track of the current page number and total count
    page_number = 1
    total_count = 0

    while True:
        url = base_url + f"&page={page_number}"
        driver.get(url)

        # Wait for dynamic content to load (you may need to adjust the waiting time)
        time.sleep(10)

        # Use BeautifulSoup to find the parent element containing all the product listings
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.find_all("div", {"data-component-type": "s-search-result"})

        with open("scraped_products.txt", "a", encoding="utf-8") as file:
            for product in products:
                try:
                    product_name_elem = product.find("span", class_="a-size-base-plus a-color-base a-text-normal")
                    product_price_elem = product.find("span", class_="a-offscreen")
                    product_url_elem = product.find("a", class_="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal")

                    if product_name_elem and product_price_elem and product_url_elem:
                        product_name = product_name_elem.text.strip()
                        product_price = product_price_elem.text.strip()
                        product_url = "https://www.amazon.nl" + product_url_elem["href"]

                        file.write(f"Product Name: {product_name}\n")
                        file.write(f"Product Price: {product_price}\n")
                        file.write(f"Product URL: {product_url}\n")
                        file.write("-" * 30 + "\n")
                        total_count += 1
                    else:
                        logging.warning("Error: Product details not found.")
                except NoSuchElementException as e:
                    logging.warning(f"Error scraping product: {e}")

        # Check if there are more pages of results
        next_page_elem = driver.find_elements(By.CSS_SELECTOR, ".s-pagination-next")
        if len(next_page_elem) == 0 or not next_page_elem[0].is_enabled():
            break  # Stop if there are no more pages or the "Next Page" button is disabled
        else:
            try:
                driver.execute_script("arguments[0].click();", next_page_elem[0])
                page_number += 1
                logging.info(f"Switching to page {page_number}")
            except Exception as e:
                logging.warning(f"Error switching to next page: {e}")
                break  # Stop if there is an error clicking the "Next Page" button

    driver.quit()

    # Write the total count to the file
    with open("scraped_products.txt", "a", encoding="utf-8") as file:
        file.write(f"Total products found for '{search_term}': {total_count}\n")

if __name__ == "__main__":
    scrape_amazon()
