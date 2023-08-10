import logging
from tkinter import *
from tkinter import ttk
import tkinter as tk
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import winshell
import shutil
import threading  # Import threading to run scraping process in a separate thread
import time

class AmazonScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AWS")

        # Determine the images directory path in the Documents folder
        documents_folder = os.path.expanduser("~/Documents")
        images_path = os.path.join(documents_folder, "images")
        image_path = os.path.join(images_path, "aws.png")

        # Create the "images" directory if it doesn't exist
        if not os.path.exists(images_path):
            os.makedirs(images_path)

            # Copy the "aws.png" file into the "images" directory
            shutil.copy("aws.png", image_path)

        # Open and resize the logo image
        logo_image = Image.open(image_path)
        logo_icon = ImageTk.PhotoImage(logo_image)

        # Set the window icon
        self.root.iconphoto(True, logo_icon)

        # Maximize the window
        self.root.state('zoomed')

        self.surrounding_frame = Frame(root, bg="grey95")
        self.surrounding_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Frame for the search section
        self.frame_search = Frame(self.surrounding_frame, padx=20, pady=20, bg="lightblue", borderwidth=2, relief="solid", highlightbackground="grey")
        self.frame_search.grid(row=0, column=0, sticky="nw")

        # Search elements
        self.label = Label(self.frame_search, text="Enter search term:", font=("Helvetica", 12))
        self.label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.search_entry = Entry(self.frame_search, font=("Helvetica", 12))
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        self.search_button = Button(self.frame_search, text="Search", command=self.start_scraping,
                                    font=("Helvetica", 7))
        self.search_button.grid(row=1, column=2, sticky="w", padx=0.1, pady=5)

        # Match the height of the search button to the search entry
        entry_height = self.search_entry.winfo_height()
        self.search_button.config(height=entry_height)

        self.results_frame = Frame(root)
        self.results_frame.pack(padx=10, pady=5)

        self.results_frame = Frame(root)
        self.results_frame.pack(padx=10, pady=5)

        # Create a label for the percentage counter
        self.percentage_label = Label(self.results_frame, text="", font=("Helvetica", 12))
        self.percentage_label.pack()

        self.results_tree = ttk.Treeview(self.results_frame, columns=("Name", "Price", "URL"), show="headings")
        self.results_tree.heading("Name", text="Product Name")
        self.results_tree.heading("Price", text="Product Price")
        self.results_tree.heading("URL", text="Product URL")

        self.results_tree.column("Name", width=580, anchor="w")
        self.results_tree.column("Price", width=100, anchor="center")
        self.results_tree.column("URL", width=580, anchor="w")

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 10), rowheight=45)
        style.configure("Treeview.Heading", background="lightblue")

        self.results_tree.pack(side="left", fill="both", expand=True)

        vertical_scrollbar = Scrollbar(self.results_frame, orient="vertical", command=self.results_tree.yview)
        vertical_scrollbar.pack(side="right", fill="y")
        self.results_tree.configure(yscrollcommand=vertical_scrollbar.set)

        # Move the Stop button below the search frame
        self.exit_button = Button(self.surrounding_frame, text="Stop Program", command=self.exit_program, bg="red")
        self.exit_button.grid(row=1, column=0, sticky="sw", padx=0, pady=10)

        # Attach the progress bar to the top of the columns
        self.progress_bar = ttk.Progressbar(self.results_frame, mode="determinate", maximum=100, length=1260)
        self.progress_bar.place(relx=0.5, rely=0.03, anchor="center", y=1)  # Adjust the y position as needed

        # Get the background color of the progress bar
        progress_bar_bg = ttk.Style().lookup("TProgressbar", "background")
        self.progress_bar_label = Label(self.progress_bar, text="0%", font=("Helvetica", 8),
                                        highlightthickness=0, highlightbackground=progress_bar_bg)
        self.progress_bar_label.place(relx=0.5, rely=0.5, anchor="center")

        self.is_searching = False
        self.scraping_thread = None  # Initialize scraping thread

        self.num_updates = 100  # Number of progress bar updates
        self.update_interval = 98.28 / self.num_updates  # Calculate update interval
        # Bind the event and method to update the GUI
        self.root.bind("<<UpdateResultData>>", self.on_update_result_data)

        self.is_searching = False

        self.start_time = 0  # Initialize start_time

    def update_progress(self, step):
        if step <= self.num_updates:
            progress_value = int((step / self.num_updates) * 100)
            self.progress_bar["value"] = progress_value
            self.progress_bar_label.config(text=f"{progress_value}%")  # Update the label text
            self.root.update()  # Update the GUI to reflect changes

            # Wait until the next update
            time.sleep(self.update_interval)

            # Schedule the next update
            self.update_progress(step + 1)
        else:
            # After scraping is complete, re-enable the button
            self.is_searching = False
            self.search_button.config(state="normal")  # Re-enable the search button

    def check_thread_status(self):
        if self.scraping_thread and self.scraping_thread.is_alive():
            self.root.after(1000, self.check_thread_status)
        else:
            self.search_button.config(state="normal")  # Re-enable the search button
            self.progress_bar["value"] = 0
            self.progress_bar_label.config(text="0%")
            self.search_entry.delete(0, "end")  # Clear the search entry

    def start_scraping(self):
        search_term = self.search_entry.get().strip()  # Get the search term and remove leading/trailing spaces

        if not search_term:
            messagebox.showwarning("Empty Search Term", "Please enter a search term.")
            return  # Return early if search term is empty

        if not self.is_searching:
            self.is_searching = True
            self.search_button.config(state="disabled")  # Disable the search button

            # Start the scraping process in a new thread
            self.scraping_thread = threading.Thread(target=self.scrape_amazon_thread)
            self.scraping_thread.start()

            # Start updating the progress concurrently
            self.update_progress(0)  # Start incrementing progress from 0%

            # Record start time
            self.start_time = time.time()

    def increment_progress(self, step):
        if step <= 100:
            self.progress_bar["value"] = step
            self.progress_bar_label.config(text=f"{step}%")
            self.root.update()
            time.sleep(1)
            self.increment_progress(step + 1)
        else:
            # After incrementing progress to 100%, start scraping Amazon
            self.scraping_thread = threading.Thread(target=self.scrape_amazon_thread)
            self.scraping_thread.start()

            def exit_program(self):
                self.root.destroy()  # Close the program when the "Exit" button is clicked

    def exit_program(self):
        self.root.destroy()  # Close the program when the "Exit" button is clicked

    def update_results(self):
        # Fetch and update results here
        search_term = self.search_entry.get()
        self.clear_results()
        self.scrape_amazon(search_term)

        # If still searching, schedule the next update
        if self.is_searching:
            self.root.after(1000, self.update_results)  # Update every 1 second

    def scrape_amazon_thread(self):
        # Fetch and update results here
        search_term = self.search_entry.get()
        self.clear_results()
        self.scrape_amazon(search_term)

        # After scraping is complete, re-enable the button
        self.is_searching = False
        self.search_button.config(state="normal")  # Re-enable the search button

    def setup_logger(self):
        logging.basicConfig(
            format='[%(asctime)s] [%(levelname)s]: %(message)s',
            level=logging.INFO,
            handlers=[logging.StreamHandler()]
        )

    def clear_results(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def update_result_data(self, data):
        self.root.event_generate("<<UpdateResultData>>", data=data)

    def on_update_result_data(self, event):
        data = event.data
        self.results_tree.insert("", "end", values=data)

    def scrape_amazon_thread(self):
        # Fetch and update results here
        search_term = self.search_entry.get()
        self.clear_results()

        base_url = f"https://www.amazon.nl/s?k={search_term}"

        driver_path = r"C:\Users\CasReehuis\PycharmProjects\WS&PC\chromedriver.exe"
        service = webdriver.chrome.service.Service(driver_path)
        service.start()

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(service=service, options=options)

        page_number = 1
        total_count = 0
        prices = []  # List to store prices for calculating average

        while True:
            url = base_url + f"&page={page_number}"
            driver.get(url)
            time.sleep(10)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            products = soup.find_all("div", {"data-component-type": "s-search-result"})

            for product in products:
                try:
                    product_name_elem = product.find("span", class_="a-size-base-plus a-color-base a-text-normal")
                    product_price_elem = product.find("span", class_="a-offscreen")
                    product_url_elem = product.find("a",
                                                    class_="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal")

                    if product_name_elem and product_price_elem and product_url_elem:
                        product_name = product_name_elem.text.strip()
                        product_price = product_price_elem.text.strip()
                        product_url = "https://www.amazon.nl" + product_url_elem["href"]

                        self.results_tree.insert("", "end", values=(product_name, product_price, product_url))
                        total_count += 1

                        # Append price to the list
                        try:
                            price_float = float(product_price.replace("€", "").replace(",", "."))
                            prices.append(price_float)
                        except ValueError:
                            pass  # Ignore invalid price format
                except NoSuchElementException as e:
                    logging.warning(f"Error scraping product: {e}")

            next_page_elem = driver.find_elements(By.CSS_SELECTOR, ".s-pagination-next")
            if len(next_page_elem) == 0 or not next_page_elem[0].is_enabled():
                break
            else:
                try:
                    driver.execute_script("arguments[0].click();", next_page_elem[0])
                    page_number += 1
                    logging.info(f"Switching to page {page_number}")
                except Exception as e:
                    logging.warning(f"Error switching to next page: {e}")
                    break

        driver.quit()

        if prices:
            average_price = sum(prices) / len(prices)
            low_threshold = average_price * 0.8
            high_threshold = average_price * 1.2

            for item in self.results_tree.get_children():
                price = self.results_tree.item(item, "values")[1]
                try:
                    price_float = float(price.replace("€", "").replace(".", "").replace(",", "."))
                    if price_float < low_threshold:
                        self.results_tree.tag_configure("low", background="lightblue")
                        self.results_tree.item(item, tags=("low",))
                    elif price_float > high_threshold:
                        self.results_tree.tag_configure("high", background="red")
                        self.results_tree.item(item, tags=("high",))
                    else:
                        self.results_tree.tag_configure("normal", background="lightgreen")
                        self.results_tree.item(item, tags=("normal",))
                except ValueError:
                    pass  # Ignore invalid price format

        end_time = time.time()
        elapsed_time = end_time - self.start_time

        self.results_tree.insert("", "end", values=(
            f"Total products found for '{search_term}': {total_count}",
            f"Time taken: {elapsed_time:.2f} seconds", ""))

        # After scraping is complete, re-enable the button
        self.is_searching = False
        self.search_button.config(state="normal")  # Re-enable the search button

if __name__ == "__main__":
    root = Tk()
    app = AmazonScraperGUI(root)
    root.mainloop()