import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, override

from scrapy import Item

from .queue import ScrapingQueue

T = TypeVar("T", bound=Item)

logger = logging.getLogger(__name__)

class Processor(ABC, Generic[T]):
    """Abstract base class for processors that handle Scrapy items.

    Subclasses should implement the `process` method to define how items
    are processed in the queue.
    """

    def __init__(self, queue: ScrapingQueue[T]) -> None:
        """Initializes the processor with a ScrapingQueue.

        Args:
            queue (ScrapingQueue[T]): The queue that holds the items to process.
        """
        self._queue = queue

    @abstractmethod
    def process(self) -> None:
        """Processes the items in the queue.
        This method must be implemented by subclasses to define processing logic.
        """
        pass

    @property
    def queue(self) -> ScrapingQueue[T]:
        """Returns the queue that the processor is working with.

        Returns:
            ScrapingQueue[T]: The queue of items to be processed.
        """
        return self._queue


class ItemProcessor(Processor[T]):
    """Concrete implementation of Processor for processing items.

    This class processes batches of items from the queue and can be customized
    by overriding `process_item` for item-specific logic.
    """

    @override
    def process(self) -> None:
        """Processes batches of items from the queue.

        This method retrieves batches of items from the queue and processes
        each batch by passing items to the `process_batch` method.
        """
        try:
            for batch in self.queue.get_batches():
                self.process_batch(batch)
        except Exception as e:
            logger.error("Error processing items from the queue", exc_info=e)
            raise e
        finally:
            self.queue.close()

    def process_batch(self, batch: list[T]) -> None:
        """Processes a batch of items.

        This method is called for each batch of items and processes each item
        using the `process_item` method.

        Args:
            batch (list[T]): A list of items to process.
        """
        logger.info(f"Processing batch of {len(batch)} items.")
        for item in batch:
            self.process_item(item)

    def process_item(self, item: T) -> None:
        """Processes an individual item.

        This method can be overridden by subclasses to define custom item processing.

        Args:
            item (T): The item to process.
        """
        # Default implementation: just print the item
        print(item)
