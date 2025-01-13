import logging
from dataclasses import dataclass, field
from typing import Any, ParamSpec, Self, TypeVar

from scrapy import Item, Spider, signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from twisted.internet.threads import deferToThread

from .processor import Processor
from .queue import ScrapingQueue

T = TypeVar("T", bound=Item)
P = ParamSpec("P")

logger = logging.getLogger(__name__)

@dataclass(kw_only=True)
class Signals:
    """Context manager for managing Scrapy signals during a crawl.

    This class connects and disconnects callbacks for Scrapy's signals such as
    `item_scraped` and `engine_stopped`. It also handles the stopping of the
    Scrapy crawler and closing the associated queue when necessary.
    """
    queue: ScrapingQueue[Item]
    
    _stopping: bool = field(default=False, init=False)
    _crawler: CrawlerProcess | None = field(default=None, init=False)

    def on_item_scraped(self, item: Item) -> None:
        """Callback triggered when an item is scraped.

        This method will put the item into the queue if it's not closed, or stop
        the crawler if the queue is closed.

        Args:
            item (Item): The scraped item.
        """
        if not self.queue.is_closed:
            self.queue.put(item)
        else:
            self._stop_crawler("Queue is closed, stopping")

    def on_engine_stopped(self) -> None:
        """Callback triggered when the Scrapy engine stops.

        This method ensures the queue is closed and the crawler is stopped when
        the engine stops.
        """
        self._stopping = True
        if self._crawler:
            self._crawler.stop()
        self.queue.close()

    def _stop_crawler(self, message: str) -> None:
        """Stops the crawler with a log message.

        This method will log a message and ensure the crawler is stopped if it
        has not already been stopped.

        Args:
            message (str): Message to log before stopping the crawler.
        """
        logger.info(message)
        if not self._stopping:
            self.on_engine_stopped()

    def __call__(self, crawler: CrawlerProcess) -> Self:
        """Sets the crawler instance.

        This method allows for method chaining when setting the `crawler` instance.

        Args:
            crawler (CrawlerProcess): The Scrapy crawler instance.

        Returns:
            Signals: The current instance for method chaining.
        """
        self._crawler = crawler
        return self

    def __enter__(self) -> None:
        """Connects the signals to the Scrapy dispatcher.

        This method is called when entering the `with` block. It connects the
        `on_item_scraped` and `on_engine_stopped` callbacks to the respective
        Scrapy signals.
        """
        dispatcher.connect(self.on_item_scraped, signals.item_scraped)
        dispatcher.connect(self.on_engine_stopped, signals.engine_stopped)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Disconnects the signals from the Scrapy dispatcher.

        This method is called when exiting the `with` block. It disconnects the
        `on_item_scraped` and `on_engine_stopped` callbacks from the Scrapy signals.
        """
        dispatcher.disconnect(self.on_item_scraped, signals.item_scraped)
        dispatcher.disconnect(self.on_engine_stopped, signals.engine_stopped)


@dataclass(kw_only=True)
class ScrapyRunner:
    """Wrapper for running Scrapy spiders with custom item processing and queue management.

    This class handles the initialization of the Scrapy spider, item processor, and queue.
    It also manages the lifecycle of the Scrapy crawler and coordinates the running of the
    spider with item processing.
    """
    spider: type[Spider]
    processor: type[Processor[Item]]
    processor_kwargs: dict[str, Any] = field(default_factory=dict)
    queue: ScrapingQueue[Item] = field(default_factory=lambda: ScrapingQueue[Item]())
    scrapy_settings: dict[str, Any] = field(default_factory=dict)

    _crawler: CrawlerProcess = field(init=False)
    _processor_instance: Processor[Item] = field(init=False)
    _signals: Signals = field(init=False)

    def __post_init__(self) -> None:
        """Post initialization logic for setting up the processor, signals, and crawler.

        This method is called after the dataclass initialization to configure the
        necessary components like the processor, signals, and crawler process.
        """
        self._processor_instance = self.processor(queue=self.queue, **self.processor_kwargs)
        self._signals = Signals(queue=self.queue)
        self._crawler = CrawlerProcess(
            settings={
                "LOG_LEVEL": "INFO",
                "TELNETCONSOLE_ENABLED": False,
                **self.scrapy_settings,
            },
        )

    def run(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """Runs the Scrapy crawler and starts processing items in the queue.

        This method starts the Scrapy crawler and begins processing items asynchronously.
        The items are processed by the processor while the spider runs.

        Args:
            *args: Positional arguments to pass to the spider.
            **kwargs: Keyword arguments to pass to the spider.
        """
        # Start item processing asynchronously in a separate thread
        deferToThread(self._processor_instance.process)

        try:
            logger.info("Starting Scrapy crawler")
            with self._signals(self._crawler):
                self._crawler.crawl(self.spider, *args, **kwargs)
                self._crawler.start(stop_after_crawl=True)
        except Exception as e:
            logger.error("Error running the crawler", exc_info=e)
            raise e
