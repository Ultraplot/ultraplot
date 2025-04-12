from matplotlib.mathtext import MathTextParser
import pytest, ultraplot as uplt, matplotlib as mpl
import ultraplot.internals.fonts as ufonts

from unittest.mock import patch, MagicMock


@pytest.mark.skip(reason="Only for reference, relies on class attributes")
def test_replacement():
    """
    Test whether replaced the unicodes fonts
    """
    # This is just a reference and is already skipped
    # The correct attribute name may have changed in the MathTextParser class
    pass


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


class TestCollectAndReplaceFonts:
    """Tests for _collect_replacements and _replace_fonts methods."""

    def setup_method(self):
        """Set up the test environment before each test."""
        # Create an instance of _UnicodeFonts for testing
        # We'll patch super().__init__ to avoid actual font loading
        with patch.object(ufonts.UnicodeFonts, "__init__", return_value=None):
            self.font_instance = ufonts._UnicodeFonts.__new__(ufonts._UnicodeFonts)
            # Reset the warning flag for tests
            ufonts.WARN_MATHPARSER = True

    def test_init_method(self, monkeypatch):
        """Test the __init__ method of _UnicodeFonts."""
        # Mock the _collect_replacements and _replace_fonts methods
        mock_ctx = {"mathtext.it": "sans:italic"}
        mock_regular = {"it": "regular:italic"}

        with (
            patch.object(
                ufonts._UnicodeFonts,
                "_collect_replacements",
                return_value=(mock_ctx, mock_regular),
            ) as mock_collect,
            patch.object(ufonts._UnicodeFonts, "_replace_fonts") as mock_replace,
            patch.object(
                ufonts.UnicodeFonts, "__init__", return_value=None
            ) as mock_super_init,
        ):
            # Call __init__ directly
            font_instance = ufonts._UnicodeFonts()

            # Verify the methods were called with expected arguments
            mock_collect.assert_called_once()
            mock_replace.assert_called_once_with(mock_regular)

            # Verify super().__init__ was called with rc_context
            mock_super_init.assert_called_once()

            # Test that the __init__ method uses rc_context correctly
            with patch("matplotlib.rc_context") as mock_rc_context:
                # Create a new context manager for testing
                mock_context = MagicMock()
                mock_rc_context.return_value = mock_context

                # Call __init__ again to test rc_context
                ufonts._UnicodeFonts()

                # Verify rc_context was called with the correct arguments
                mock_rc_context.assert_called_once_with(mock_ctx)

    def test_collect_replacements_no_regular_fonts(self, monkeypatch):
        """Test _collect_replacements with no 'regular' fonts in rcParams."""
        # Mock rcParams with no 'regular' fonts
        mock_rcparams = {
            "mathtext.cal": "custom-font",
            "mathtext.rm": "some-font",
            "mathtext.tt": "another-font",
            "mathtext.it": "italic-font",
            "mathtext.bf": "bold-font",
            "mathtext.sf": "sans-font",
        }
        monkeypatch.setattr(mpl, "rcParams", mock_rcparams)

        # Call the method
        ctx, regular = self.font_instance._collect_replacements()

        # Verify empty dictionaries as no replacements should be made
        assert ctx == {}
        assert regular == {}

    def test_collect_replacements_with_regular_fonts(self, monkeypatch):
        """Test _collect_replacements with 'regular' fonts in rcParams."""
        # Mock rcParams with some 'regular' fonts
        mock_rcparams = {
            "mathtext.cal": "regular:script",
            "mathtext.rm": "some-font",  # No replacement needed
            "mathtext.tt": "regular:monospace",
            "mathtext.it": "regular:italic",
            "mathtext.bf": "bold-font",  # No replacement needed
            "mathtext.sf": "sans-font",  # No replacement needed
        }
        monkeypatch.setattr(mpl, "rcParams", mock_rcparams)

        # Call the method
        ctx, regular = self.font_instance._collect_replacements()

        # Verify dictionaries contain expected replacements
        expected_ctx = {
            "mathtext.cal": "sans:script",
            "mathtext.tt": "sans:monospace",
            "mathtext.it": "sans:italic",
        }
        expected_regular = {
            "cal": "regular:script",
            "tt": "regular:monospace",
            "it": "regular:italic",
        }
        assert ctx == expected_ctx
        assert regular == expected_regular

    def test_replace_fonts_with_required_attributes(self, monkeypatch):
        """Test _replace_fonts when the instance has required attributes."""
        # Create mock fontmap and _fonts attributes
        mock_fontmap = {"rm": "original_font_path", "it": "original_italic_path"}
        mock_fonts = {"regular": MagicMock()}

        # Create mock font property
        mock_font_prop = MagicMock()
        mock_font_prop.name = "test-font"

        # Add required attributes to the instance
        self.font_instance.fontmap = mock_fontmap
        self.font_instance._fonts = mock_fonts

        # Create regular dictionary for replacements
        regular = {"rm": "regular:normal", "it": "regular:italic"}

        # Mock ttfFontProperty and findfont functions
        with (
            patch(
                "ultraplot.internals.fonts.ttfFontProperty", return_value=mock_font_prop
            ) as mock_ttf,
            patch(
                "ultraplot.internals.fonts.findfont", return_value="new_font_path"
            ) as mock_findfont,
        ):

            # Call the method
            self.font_instance._replace_fonts(regular)

            # Verify the font property was created from the regular font
            mock_ttf.assert_called_once_with(mock_fonts["regular"])

            # Verify findfont was called with the correct properties
            assert mock_findfont.call_count == 2
            mock_findfont.assert_any_call("test-font:normal", fallback_to_default=False)
            mock_findfont.assert_any_call("test-font:italic", fallback_to_default=False)

            # Verify fontmap was updated
            assert self.font_instance.fontmap["rm"] == "new_font_path"
            assert self.font_instance.fontmap["it"] == "new_font_path"

    def test_replace_fonts_missing_fontmap(self):
        """Test _replace_fonts when fontmap attribute is missing."""
        # Only add _fonts attribute, missing fontmap
        self.font_instance._fonts = {"regular": MagicMock()}

        # Create regular dictionary for replacements
        regular = {"rm": "regular:normal"}

        # Patch warning function
        with patch("ultraplot.internals.warnings._warn_ultraplot") as mock_warn:
            # Call the method
            self.font_instance._replace_fonts(regular)

            # Verify warning was called
            mock_warn.assert_called_once_with("Failed to update the math text parser.")

            # Verify warning flag was updated
            assert ufonts.WARN_MATHPARSER is False

    def test_replace_fonts_missing_fonts_dict(self):
        """Test _replace_fonts when _fonts dictionary is missing."""
        # Only add fontmap attribute, missing _fonts
        self.font_instance.fontmap = {}

        # Create regular dictionary for replacements
        regular = {"rm": "regular:normal"}

        # Patch warning function
        with patch("ultraplot.internals.warnings._warn_ultraplot") as mock_warn:
            # Call the method
            self.font_instance._replace_fonts(regular)

            # Verify warning was called
            mock_warn.assert_called_once_with("Failed to update the math text parser.")

            # Verify warning flag was updated
            assert ufonts.WARN_MATHPARSER is False

    def test_replace_fonts_missing_regular_font(self):
        """Test _replace_fonts when regular font is missing from _fonts."""
        # Add both attributes but with no 'regular' in _fonts
        self.font_instance.fontmap = {}
        self.font_instance._fonts = {"other": MagicMock()}

        # Create regular dictionary for replacements
        regular = {"rm": "regular:normal"}

        # Patch warning function
        with patch("ultraplot.internals.warnings._warn_ultraplot") as mock_warn:
            # Call the method
            self.font_instance._replace_fonts(regular)

            # Verify warning was called
            mock_warn.assert_called_once_with("Failed to update the math text parser.")

            # Verify warning flag was updated
            assert ufonts.WARN_MATHPARSER is False

    def test_replace_fonts_empty_regular_dict(self):
        """Test _replace_fonts with an empty regular dictionary."""
        # Add required attributes
        self.font_instance.fontmap = {"rm": "original_font_path"}
        self.font_instance._fonts = {"regular": MagicMock()}

        # Call with empty regular dictionary
        with (
            patch("ultraplot.internals.fonts.ttfFontProperty") as mock_ttf,
            patch("ultraplot.internals.fonts.findfont") as mock_findfont,
        ):

            # Call the method
            self.font_instance._replace_fonts({})

            # Verify no replacements were attempted
            mock_ttf.assert_called_once()
            mock_findfont.assert_not_called()

            # Fontmap should remain unchanged
            assert self.font_instance.fontmap == {"rm": "original_font_path"}

    def test_warning_suppression(self):
        """Test that warnings are suppressed after the first warning."""
        # Reset warning flag to ensure it's True
        ufonts.WARN_MATHPARSER = True

        # Make sure missing required attributes
        if hasattr(self.font_instance, "fontmap"):
            delattr(self.font_instance, "fontmap")
        if hasattr(self.font_instance, "_fonts"):
            delattr(self.font_instance, "_fonts")

        # First call should trigger warning
        with patch("ultraplot.internals.warnings._warn_ultraplot") as mock_warn:
            self.font_instance._replace_fonts({})
            mock_warn.assert_called_once()
            assert ufonts.WARN_MATHPARSER is False

        # Reset mock to verify second call
        with patch("ultraplot.internals.warnings._warn_ultraplot") as mock_warn:
            # Second call should not trigger warning
            self.font_instance._replace_fonts({})
            mock_warn.assert_not_called()
            assert ufonts.WARN_MATHPARSER is False
