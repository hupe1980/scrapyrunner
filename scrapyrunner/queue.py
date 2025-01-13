from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Generic, Iterator, TypeVar

T = TypeVar("T")

@dataclass
class ScrapingQueue(Queue, Generic[T]):
    """A specialized queue for handling batches of Scrapy items.

    This queue extends the standard Python `Queue` and adds functionality for
    batch processing, streaming, and gracefully closing operations. It supports
    item retrieval with a timeout and batching items for efficient processing.
    """
    maxsize: int = 0  # The maximum number of items the queue can hold (0 means unlimited size).
    batch_size: int = 10  # The size of batches returned by `get_batches`, default is 10.
    read_timeout: float = 1.0  # Timeout for reading from the queue, default is 1.0 seconds.

    _is_closed: bool = field(default=False, init=False)  # Flag to indicate if the queue is closed.

    def __post_init__(self):
        """Initializes the Queue class with the specified maxsize.

        This method is called after the dataclass initialization. It ensures
        that the parent Queue class is initialized with the given `maxsize`.
        """
        super().__init__(self.maxsize)

    def get_batches(self) -> Iterator[list[T]]:
        """Generates batches of items from the queue.

        This method continuously retrieves items from the queue and yields them
        in batches of size `batch_size`. It stops when the queue is closed or
        no more items are available. The method handles the timeout for reading
        from the queue and yields any remaining items when the queue is empty.

        Yields:
            list[T]: A batch of items from the queue.
        """
        batch: list[T] = []
        while not self._is_closed or not self.empty():
            try:
                # Retrieve an item with a timeout
                item: T = self.get(timeout=self.read_timeout)
                batch.append(item)
                self.task_done()
                if len(batch) == self.batch_size:
                    yield batch
                    batch = []
            except Empty:
                # If the queue is empty, yield any remaining items in the batch
                if batch:
                    yield batch
                    batch = []
            if batch:
                yield batch

    def stream(self) -> Iterator[list[T]]:
        """Streams batches of items from the queue.

        This method wraps the `get_batches` method and gracefully handles the
        `GeneratorExit` exception to close the queue when the generator is
        stopped by the caller.

        Yields:
            list[T]: A batch of items from the queue.
        """
        try:
            yield from self.get_batches()
        except GeneratorExit:
            self.close()

    def close(self) -> None:
        """Closes the queue, preventing further item retrieval.

        Once the queue is closed, any attempt to retrieve an item will raise
        a `QueueClosedError`. The method sets the `_is_closed` flag to True
        and ensures no more items can be added or retrieved from the queue.
        """
        self._is_closed = True

    @property
    def is_closed(self) -> bool:
        """Indicates whether the queue is closed.

        Returns:
            bool: `True` if the queue is closed, `False` otherwise.
        """
        return self._is_closed
