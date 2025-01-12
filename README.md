
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
from time import sleep
import scrapy
from scrapyrunner import ScrapyRunner, ItemProcessor

# Define a Scrapy Spider
class MySpider(scrapy.Spider):
    name = 'example'
    
    def parse(self, response):
        data = response.xpath("//title/text()").extract_first()
        return {"title": data}

# Define a custom Item Processor
class MyProcessor(ItemProcessor):
    def process_item(self, item: scrapy.Item) -> None:
        print(">>>", item, "<<<")
        sleep(2)  # Simulate a delay for processing

if __name__ == '__main__':
    # Create an instance of ScrapyRunner with the spider and processor
    scrapy_runner = ScrapyRunner(spider=MySpider, processor=MyProcessor)
    scrapy_runner.run(start_urls=["https://example.org", "https://scrapy.org"])  # Start scraping
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
settings = {
    "LOG_LEVEL": "DEBUG",
    "USER_AGENT": "MyCustomAgent",
    # Add more custom settings as needed
}

runner = ScrapyRunner(spider=MySpider, settings=settings)
runner.run(start_urls=["https://example.org"])
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
