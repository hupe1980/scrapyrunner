# Importing necessary libraries
from time import sleep  # Used to simulate a delay during item processing

import scrapy  # Scrapy library for creating spiders

from scrapyrunner import ItemProcessor, ScrapyRunner  # Importing the custom Scrapy runner and processor classes


# Define the spider to crawl a webpage and extract data
class MySpider(scrapy.Spider):
    name = 'example'  # Name of the spider, used to identify it when running

    def parse(self, response):
        # This method is called to parse the response from the URL.
        # We extract the title of the page using XPath and return it as a dictionary.
        data = response.xpath("//title/text()").extract_first()
        return {"title": data}  # Returning the extracted title in a dictionary format

# Define the item processor to process the items after they are scraped
class MyProcessor(ItemProcessor):
    def process_item(self, item: scrapy.Item) -> None:
        # A simulated delay is added here to mimic real processing time.
        # In a real-world scenario, this could be a time-consuming task like data validation or saving to a database.
        sleep(2)  # Sleep for 2 seconds to simulate processing time
        print(">>>", item, "<<<")  # Print the processed item to the console

# Main block to execute the spider and processor
if __name__ == '__main__':
    # Create an instance of ScrapyRunner with the specified spider and processor.
    # ScrapyRunner will handle crawling and managing the queue for items.
    scrapy_runner = ScrapyRunner(spider=MySpider, processor=MyProcessor)

    # Run the Scrapy crawler, passing the starting URL to the spider
    # The spider will start scraping the provided URL and the processor will handle the items.
    scrapy_runner.run(start_urls=["https://example.org"])  # Run the spider with the start URL
