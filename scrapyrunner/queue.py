import logging
from queue import Empty, Queue
from typing import Generic, Iterator, TypeVar

from scrapy import Item

T = TypeVar("T", bound=Item)

logger = logging.getLogger(__name__)


class QueueClosedError(Exception):
    """Custom exception raised when an operation is attempted on a closed queue."""
    pass


class ScrapingQueue(Queue, Generic[T]):
    """A specialized queue for handling batches of Scrapy items.

    This queue supports batch processing, streaming, and closing operations.
    It extends the standard Python `Queue` and adds functionality tailored for
    web scraping workflows.
    """

    def __init__(self, maxsize: int = 0, batch_size: int = 10, read_timeout: float = 1.0) -> None:
        """
        Initializes the ScrapingQueue.

        Args:
            maxsize (int, optional): The maximum number of items the queue can hold.
                Defaults to 0, which means unlimited size.
            batch_size (int, optional): The size of batches returned by `get_batches`.
                Defaults to 10.
            read_timeout (float, optional): Timeout in seconds for reading from the queue.
                Defaults to 1.0.
        """
        super().__init__(maxsize)
        self.batch_size = batch_size
        self.read_timeout = read_timeout
        self._is_closed = False

    def get_batches(self) -> Iterator[list[T]]:
        """Generates batches of items from the queue.

        This method continuously retrieves items from the queue and yields them in
        batches of size `batch_size`. It stops when the queue is closed or no more
        items are available.

        Yields:
            list[T]: A batch of items from the queue.

        Raises:
            QueueClosedError: If the queue is closed while attempting to retrieve items.
        """
        batch: list[T] = []
        while True:
            if len(batch) == self.batch_size:
                yield batch
                batch = []

            try:
                if self.is_closed:
                    raise QueueClosedError("Queue is closed")

                # Retrieve an item with a timeout
                item: T = self.get(timeout=self.read_timeout)
                batch.append(item)
                self.task_done()
            except Empty:
                # If queue is empty, yield any remaining items in the batch
                if batch:
                    yield batch
                    batch = []
            except QueueClosedError:
                logger.info("Queue is closed, stopping...")
                if batch:
                    yield batch
                break

    def stream(self) -> Iterator[list[T]]:
        """Streams batches of items from the queue.

        This method wraps `get_batches` and handles `GeneratorExit` to gracefully close
        the queue when the generator is stopped by the caller.

        Yields:
            list[T]: A batch of items from the queue.
        """
        try:
            yield from self.get_batches()
        except GeneratorExit:
            self.close()

    def close(self) -> None:
        """Closes the queue, preventing further item retrieval.

        Once closed, any attempt to get an item from the queue will raise
        `QueueClosedError`. Existing items in the queue can still be processed.
        """
        self._is_closed = True

    @property
    def is_closed(self) -> bool:
        """Indicates whether the queue is closed.

        Returns:
            bool: `True` if the queue is closed, `False` otherwise.
        """
        return self._is_closed
