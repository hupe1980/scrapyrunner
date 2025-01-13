import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, override

from scrapy import Item

from .queue import ScrapingQueue

T = TypeVar("T", bound=Item)

logger = logging.getLogger(__name__)

@dataclass(kw_only=True)
class Processor(ABC, Generic[T]):
    """
    Abstract base class for processors that handle Scrapy items.

    Subclasses of `Processor` must implement the `process` method to define how
    items are processed in the queue. This class provides a base structure for
    creating custom processors for batch or item-level processing.
    
    Attributes:
        queue (ScrapingQueue[T]): The queue that holds the items to be processed.
    """
    queue: ScrapingQueue[T]

    @abstractmethod
    def process(self) -> None:
        """
        Processes the items in the queue.

        This method must be implemented by subclasses to define specific processing logic,
        such as item manipulation, validation, or other operations.
        """
        pass


@dataclass(kw_only=True)
class ItemProcessor(Processor[T]):
    """
    Concrete implementation of the `Processor` for processing items.

    This class retrieves batches of items from the queue and processes each batch by
    calling the `process_batch` method. It also provides a default implementation
    for processing individual items via `process_item`. Subclasses can override
    `process_item` for custom item-specific logic.

    Attributes:
        queue (ScrapingQueue[T]): The queue that holds the items to be processed.
    """

    @override
    def process(self) -> None:
        """
        Processes batches of items from the queue.

        This method continuously retrieves batches of items from the queue and processes
        each batch by calling the `process_batch` method. It also handles any exceptions
        that may occur during the processing, logging errors, and ensures the queue is closed
        after processing completes.

        Raises:
            Exception: If an error occurs during item processing, the exception is logged and raised again.
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
        """
        Processes a batch of items.

        This method is called for each batch of items. By default, it processes each
        item in the batch by calling the `process_item` method, but it can be customized
        by subclasses to implement batch-specific logic.

        Args:
            batch (list[T]): A list of items to process.
        """
        logger.info(f"Processing batch of {len(batch)} items.")
        for item in batch:
            self.process_item(item)

    def process_item(self, item: T) -> None:
        """
        Processes an individual item.

        This method provides a default implementation that simply prints the item.
        Subclasses can override this method to implement custom processing logic, such as
        validation, manipulation, or transformation of the item.

        Args:
            item (T): The item to process.
        """
        # Default implementation: prints the item to the console
        print(item)
