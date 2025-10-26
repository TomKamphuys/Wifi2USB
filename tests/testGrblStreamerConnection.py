import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from wifi_2_usb.client_connection import GrblStreamerClientConnection


class TestGrblStreamerClientConnection:
    """Test suite for GrblStreamerClientConnection class."""

    @pytest.fixture
    def mock_grbl_streamer(self):
        """Create a mock GrblStreamer instance."""
        with patch('wifi_2_usb.client_connection.GrblStreamer') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_time_sleep(self):
        """Mock time.sleep to speed up tests."""
        with patch('wifi_2_usb.client_connection.time.sleep') as mock:
            yield mock

    @pytest.fixture
    def connection(self, mock_grbl_streamer, mock_time_sleep):
        """Create a GrblStreamerClientConnection instance with mocked dependencies."""
        return GrblStreamerClientConnection()

    def test_init_creates_grbl_streamer(self, mock_grbl_streamer, mock_time_sleep):
        """Test that __init__ properly initializes GrblStreamer."""
        connection = GrblStreamerClientConnection()

        # Verify GrblStreamer was created with a callback
        assert connection._grbl_streamer == mock_grbl_streamer

    def test_init_configures_grbl_streamer(self, mock_time_sleep):
        """Test that __init__ configures GrblStreamer with correct settings."""
        with patch('wifi_2_usb.client_connection.GrblStreamer') as mock_grbl_class:
            mock_instance = MagicMock()
            mock_grbl_class.return_value = mock_instance

            connection = GrblStreamerClientConnection()

            # Verify setup_logging was called
            mock_instance.setup_logging.assert_called_once()

            # Verify connection was established
            mock_instance.cnect.assert_called_once_with('/dev/ttyUSB0', 115200)

            # Verify sleep was called (waiting for connection)
            mock_time_sleep.assert_called_once_with(3)

            # Verify incremental streaming was enabled
            assert mock_instance.incremental_streaming is True

    def test_init_sets_empty_received_message(self, connection):
        """Test that __init__ initializes _received_message as empty string."""
        assert connection._received_message == ''

    def test_send_calls_send_immediately(self, connection, mock_grbl_streamer):
        """Test that send() calls GrblStreamer's send_immediately method."""
        test_message = "G0 X10 Y20"

        connection.send(test_message)

        mock_grbl_streamer.send_immediately.assert_called_once_with(test_message)

    def test_send_with_empty_string(self, connection, mock_grbl_streamer):
        """Test that send() works with empty string."""
        connection.send("")

        mock_grbl_streamer.send_immediately.assert_called_once_with("")

    def test_receive_returns_message(self, connection):
        """Test that receive() returns the stored message."""
        connection._received_message = "ok"

        result = connection.receive()

        assert result == "ok"

    def test_receive_clears_message(self, connection):
        """Test that receive() clears the message after returning it."""
        connection._received_message = "ok"

        connection.receive()

        assert connection._received_message == ''

    def test_receive_empty_message(self, connection):
        """Test that receive() returns empty string when no message."""
        result = connection.receive()

        assert result == ''

    def test_receive_multiple_calls(self, connection):
        """Test that multiple receive() calls work correctly."""
        connection._received_message = "first"

        first_result = connection.receive()
        assert first_result == "first"
        assert connection._received_message == ''

        second_result = connection.receive()
        assert second_result == ''

    def test_close_calls_disconnect(self, connection, mock_grbl_streamer):
        """Test that close() calls GrblStreamer's disconnect method."""
        connection.close()

        mock_grbl_streamer.disconnect.assert_called_once()

    def test_on_grbl_event_with_rx_buffer_percent(self, connection):
        """Test that _on_grbl_event sets received_message on rx_buffer_percent event."""
        connection._on_grbl_event("on_rx_buffer_percent")

        assert connection._received_message == 'ok'

    def test_on_grbl_event_with_other_events(self, connection):
        """Test that _on_grbl_event doesn't set message for other events."""
        connection._received_message = ''

        connection._on_grbl_event("some_other_event", "data1", "data2")

        assert connection._received_message == ''

    def test_on_grbl_event_with_data(self, connection):
        """Test that _on_grbl_event handles event data correctly."""
        # This test verifies the method runs without errors with various data types
        connection._on_grbl_event("test_event", "string", 123, 45.67, True)

        # Should not raise any exceptions

    def test_on_grbl_event_formats_data_as_strings(self, connection):
        """Test that _on_grbl_event converts data to strings for logging."""
        # We can't easily test logging output, but we can verify the method executes
        connection._on_grbl_event("test", 123, 45.67, None, True)

        # Method should complete without errors

    def test_callback_is_passed_to_grbl_streamer(self, mock_time_sleep):
        """Test that the callback function is properly passed to GrblStreamer."""
        with patch('wifi_2_usb.client_connection.GrblStreamer') as mock_grbl_class:
            mock_instance = MagicMock()
            mock_grbl_class.return_value = mock_instance

            connection = GrblStreamerClientConnection()

            # Get the callback that was passed to GrblStreamer
            callback = mock_grbl_class.call_args[0][0]

            # Verify it's the _on_grbl_event method
            assert callback == connection._on_grbl_event

    def test_event_callback_integration(self, mock_time_sleep):
        """Test that event callback properly updates received_message."""
        with patch('wifi_2_usb.client_connection.GrblStreamer') as mock_grbl_class:
            mock_instance = MagicMock()
            mock_grbl_class.return_value = mock_instance

            connection = GrblStreamerClientConnection()

            # Get the callback
            callback = mock_grbl_class.call_args[0][0]

            # Simulate callback being triggered
            callback("on_rx_buffer_percent")

            # Verify message was set
            assert connection.receive() == 'ok'

    def test_send_receive_workflow(self, connection, mock_grbl_streamer):
        """Test a typical send/receive workflow."""
        # Send a command
        connection.send("G0 X10")
        mock_grbl_streamer.send_immediately.assert_called_once_with("G0 X10")

        # Simulate receiving a response
        connection._on_grbl_event("on_rx_buffer_percent")

        # Receive the response
        response = connection.receive()
        assert response == 'ok'

        # Verify message is cleared
        assert connection.receive() == ''

    def test_multiple_events_overwrite_message(self, connection):
        """Test that multiple events overwrite the received message."""
        connection._on_grbl_event("on_rx_buffer_percent")
        assert connection._received_message == 'ok'

        # Another event of same type - message stays the same
        connection._on_grbl_event("on_rx_buffer_percent")
        assert connection._received_message == 'ok'

        # Receive clears it
        connection.receive()
        assert connection._received_message == ''

    def test_connection_implements_iclient_connection(self, connection):
        """Test that GrblStreamerClientConnection implements required interface methods."""
        from wifi_2_usb.client_connection import IClientConnection

        assert isinstance(connection, IClientConnection)
        assert hasattr(connection, 'send')
        assert hasattr(connection, 'receive')
        assert hasattr(connection, 'close')
        assert callable(connection.send)
        assert callable(connection.receive)
        assert callable(connection.close)
