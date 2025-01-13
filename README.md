
# ScrapyRunner

A Python library to run Scrapy spiders directly from your code.

## Overview

ScrapyRunner is a lightweight library that enables you to run Scrapy spiders in your Python code, process scraped items using custom processors, and manage Scrapy signals seamlessly. It simplifies the process of starting and managing Scrapy spiders and integrates well with your existing Python workflows.

## Features

- Run Scrapy spiders directly from Python code.
- Process scraped items in batches with a custom processor.
- Manage Scrapy signals (e.g., on item scraped, on engine stopped).
- Easy integration with the Scrapy framework.
- Asynchronous processing of items using Twisted.

## Installation

To install ScrapyRunner, you can use `pip`:

```bash
pip install scrapyrunner
```

## Usage

### Example

```python
# Importing necessary libraries
from dataclasses import dataclass  # Used to create data classes for the processor
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
@dataclass(kw_only=True)
class MyProcessor(ItemProcessor):
    prefix: str
    suffix: str

    def process_item(self, item: scrapy.Item) -> None:
        # A simulated delay is added here to mimic real processing time.
        # In a real-world scenario, this could be a time-consuming task like data validation or saving to a database.
        print(self.prefix, item, self.suffix)  # Print the processed item to the console
        sleep(2)  # Sleep for 2 seconds to simulate processing time

# Main block to execute the spider and processor
if __name__ == '__main__':
    # Create an instance of ScrapyRunner with the specified spider and processor.
    # ScrapyRunner will handle crawling and managing the queue for items.
    scrapy_runner = ScrapyRunner(spider=MySpider, processor=MyProcessor, processor_kwargs={"prefix": ">>>", "suffix": "<<<"})

    # Run the Scrapy crawler, passing the starting URL to the spider
    # The spider will start scraping the provided URL and the processor will handle the items.
    scrapy_runner.run(start_urls=["https://example.org", "https://scrapy.org"])  # Run the spider with the start URL
```

### How it works:

1. **Define a Spider**: In this example, `MySpider` extracts the title of a webpage.
2. **Define a Processor**: `MyProcessor` processes scraped items (here it simply sleeps for 2 seconds to simulate real processing).
3. **Run the ScrapyRunner**: The `ScrapyRunner` class is used to run the spider and process the items. The `run()` method triggers the scraping, and each item scraped is passed to the custom processor.

## Customization

### Custom Processor

To create your own custom processor:

1. Subclass `ItemProcessor`.
2. Override the `process_item()` method to handle scraped items.
3. Process each item as needed (e.g., save to a database, perform additional transformations, etc.).

```python
class MyCustomProcessor(ItemProcessor):
    def process_item(self, item: scrapy.Item) -> None:
        # Custom processing logic goes here
        print("Processing item:", item)
```

### Custom Settings

You can pass custom Scrapy settings to `ScrapyRunner`:

```python
scrapy_settings = {
    "LOG_LEVEL": "DEBUG",
    "USER_AGENT": "MyCustomAgent",
    # Add more custom settings as needed
}

runner = ScrapyRunner(spider=MySpider, processor=MyProcessor, scrapy_settings=scrapy_settings)
runner.run(start_urls=["https://example.org", "https://scrapy.org"])
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
