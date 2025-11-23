"""Unit test configuration - no external dependencies.

Unit tests should NOT use database fixtures or any external services.
If a test needs DB, move it to integration/.
"""

import pytest

# Register unit marker for all tests in this directory
pytestmark = pytest.mark.unit
