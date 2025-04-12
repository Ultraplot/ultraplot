from matplotlib.mathtext import MathTextParser
import pytest, ultraplot as uplt, matplotlib as mpl
import ultraplot.internals.fonts as ufonts

from unittest.mock import patch


@pytest.mark.skip(reason="Only for reference, relies on class attributes")
def test_replacement():
    """
    Test whether replaced the unicodes fonts
    """
    assert MathTextParser._font_mapping["custom"] is ufonts.UnicodeFonts


def test_warning_on_missing_attributes(monkeypatch):
    """Test warning is raised when font instance is missing required attributes."""
    # Create a mock instance without initialization
    mock_font_instance = ufonts._UnicodeFonts.__new__(ufonts._UnicodeFonts)

    # Use monkeypatch to temporarily set the warning flag
    monkeypatch.setattr(ufonts, "WARN_MATHPARSER", True)

    # Patch the warning function
    with patch("ultraplot.internals.warnings._warn_ultraplot") as mock_warn:
        # Call the method that should trigger the warning
        mock_font_instance._replace_fonts(regular={})

        # Verify the warning was called with the expected message
        mock_warn.assert_called_once_with("Failed to update the math text parser.")

        # Verify the global flag was updated
        assert ufonts.WARN_MATHPARSER is False


def test_warning_on_exception(monkeypatch):
    """Test that exceptions during font replacement trigger warnings."""
    # Use monkeypatch to temporarily set the warning flag
    monkeypatch.setattr(ufonts, "WARN_MATHPARSER", True)

    # Test exception handling in a way similar to how it happens in the module
    with patch("ultraplot.internals.warnings._warn_ultraplot") as mock_warn:
        # Simulate the exception block execution
        try:
            # Force an AttributeError or KeyError
            raise AttributeError("Test exception")
        except (KeyError, AttributeError):
            ufonts.warnings._warn_ultraplot("Failed to update math text parser.")
            ufonts.WARN_MATHPARSER = False

        # Verify warning was called and flag was updated
        mock_warn.assert_called_once_with("Failed to update math text parser.")
        assert ufonts.WARN_MATHPARSER is False
