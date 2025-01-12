import pytest
from scrapy import Field, Item

from scrapyrunner import ItemProcessor, ScrapingQueue


class MockItem(Item):
    """A test item for mocking Scrapy items."""
    title = Field()

@pytest.fixture
def mock_queue(mocker):
    """Fixture that creates a mock queue."""
    queue = mocker.MagicMock(ScrapingQueue[Item])

    # Create mock items using the correct syntax for Scrapy Item
    item1 = MockItem(title="Test Item 1")
    item2 = MockItem(title="Test Item 2")

    queue.get_batches.return_value = [[item1, item2]]

    return queue

@pytest.fixture
def processor(mock_queue):
    """Fixture that creates an ItemProcessor instance with a mocked queue."""
    return ItemProcessor(queue=mock_queue)

def test_processor_initialization(mock_queue, processor):
    """Test the initialization of the ItemProcessor."""
    # Verify that the processor is initialized with the correct queue
    assert processor.queue == mock_queue

def test_process_batch(processor, mock_queue, mocker):
    """Test processing a batch of items."""
    # Mock print to verify the output
    mock_process_batch = mocker.spy(processor, 'process_batch')

    # Run the process method
    processor.process()

    mock_process_batch.assert_called_once_with([MockItem(title="Test Item 1"), MockItem(title="Test Item 2")])

def test_process_item(processor, mock_queue, mocker):
    """Test processing an individual item."""
    # Mock the method process_item to assert it's being called
    mock_process_item = mocker.spy(processor, 'process_item')

    # Run the process method
    processor.process()

    # Check if process_item is called for each item in the batch
    assert mock_process_item.call_count == 2  # 2 items in the batch
    mock_process_item.assert_any_call(MockItem(title="Test Item 1"))
    mock_process_item.assert_any_call(MockItem(title="Test Item 2"))

def test_process_item_direct(processor, mock_queue, mocker):
    """Test processing an individual item."""
    # Mock print to verify the output (since process_item uses print in the default implementation)
    mock_print = mocker.patch("builtins.print")

    # Test an individual item processing
    processor.process_item(MockItem(title="Test Item"))

    # Assert that print was called with the correct item
    mock_print.assert_called_once_with(MockItem(title="Test Item"))

def test_process_with_error_handling(processor, mock_queue, mocker):
    """Test error handling during item processing."""
    # Mock the get_batches method to raise an exception
    mock_queue.get_batches.side_effect = Exception("Processing error")

    # Run the process method and check if it raises the exception
    with pytest.raises(Exception): # noqa: B017
        processor.process()

    # Verify that the queue's close method was still called
    mock_queue.close.assert_called_once()

def test_queue_closure(processor, mock_queue):
    """Test that the queue is properly closed after processing."""
    # Run the process method
    processor.process()

    # Verify that the queue's close method was called
    mock_queue.close.assert_called_once()

