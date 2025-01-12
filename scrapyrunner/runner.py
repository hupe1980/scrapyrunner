import logging
from typing import Any, ParamSpec, TypeVar

from scrapy import Item, Spider, signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from twisted.internet.threads import deferToThread

from .processor import Processor
from .queue import ScrapingQueue

T = TypeVar("T", bound=Item)
P = ParamSpec("P")

logger = logging.getLogger(__name__)


class Signals:
    """Context manager for managing Scrapy signals during a crawl.

    This class handles the connection and disconnection of Scrapy signals, as well as
    stopping the crawler gracefully when certain conditions are met.
    """

    def __init__(self, queue: ScrapingQueue[Item]) -> None:
        """
        Initializes the Signals context wrapper.

        Args:
            queue (ScrapingQueue[Item]): The queue to store scraped items.
        """
        self.stopping = False
        self.queue = queue
        self.crawler: CrawlerProcess | None = None

    def on_item_scraped(self, item: Item) -> None:
        """Callback triggered when an item is scraped.

        Args:
            item (Item): The scraped item.
        """
        if not self.queue.is_closed:
            self.queue.put(item)
        else:
            self._stop_crawler("Queue is closed, stopping")

    def on_engine_stopped(self) -> None:
        """Callback triggered when the Scrapy engine stops."""
        self.stopping = True
        if self.crawler:
            self.crawler.stop()
        self.queue.close()

    def _stop_crawler(self, message: str) -> None:
        """Stops the crawler with a log message.

        Args:
            message (str): Message to log before stopping the crawler.
        """
        logger.info(message)
        if not self.stopping:
            self.on_engine_stopped()

    def __call__(self, crawler: CrawlerProcess) -> "Signals":
        """Sets the crawler instance.

        Args:
            crawler (CrawlerProcess): The Scrapy crawler instance.

        Returns:
            Signals: The current instance for method chaining.
        """
        self.crawler = crawler
        return self

    def __enter__(self) -> None:
        """Connects the signals to the Scrapy dispatcher."""
        dispatcher.connect(self.on_item_scraped, signals.item_scraped)
        dispatcher.connect(self.on_engine_stopped, signals.engine_stopped)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Disconnects the signals from the Scrapy dispatcher."""
        dispatcher.disconnect(self.on_item_scraped, signals.item_scraped)
        dispatcher.disconnect(self.on_engine_stopped, signals.engine_stopped)


class ScrapyRunner:
    """Wrapper for running Scrapy spiders with custom item processing and queue management."""

    def __init__(
        self,
        spider: type[Spider],
        processor: type[Processor[Item]],
        queue: ScrapingQueue[Item] | None = None,
        scrapy_settings: dict[str, Any] | None = None,
    ) -> None:
        """
        Initializes the ScrapyRunner.

        Args:
            spider (type[Spider]): The Scrapy spider class to run.
            processor (type[Processor[Item]]): The processor class to handle queue items.
            queue (ScrapingQueue[Item], optional): The queue to store scraped items.
                Defaults to a new instance of ScrapingQueue.
            scrapy_settings (dict[str, Any], optional): Custom Scrapy settings.
                Defaults to basic settings with log level set to "INFO".
        """
        self.spider = spider
        self.queue = queue if queue is not None else ScrapingQueue[Item]()
        self.processor = processor(queue=self.queue)
        self.signals = Signals(queue=self.queue)
        self.crawler = CrawlerProcess(
            settings={
                "LOG_LEVEL": "INFO",
                "TELNETCONSOLE_ENABLED": False,
                **(scrapy_settings or {}),
            },
        )

    def run(self, *args, **kwargs) -> None:
        """Runs the Scrapy crawler and starts processing items in the queue.

        Args:
            *args: Positional arguments to pass to the spider.
            **kwargs: Keyword arguments to pass to the spider.
        """
        # Start item processing asynchronously in a separate thread
        deferToThread(self.processor.process)

        try:
            logger.info("Starting Scrapy crawler")
            with self.signals(self.crawler):
                self.crawler.crawl(self.spider, *args, **kwargs)
                self.crawler.start(stop_after_crawl=True)
        except Exception as e:
            logger.error("Error running the crawler", exc_info=e)
            raise e
