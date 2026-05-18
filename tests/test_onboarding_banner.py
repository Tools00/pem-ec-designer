"""Tests for ui/onboarding_banner — dismiss-once behaviour."""

from __future__ import annotations

import pytest

from pem_ec_designer.ui import qt_env  # noqa: F401

from PySide6.QtWidgets import QApplication  # noqa: E402

from pem_ec_designer.ui.onboarding_banner import OnboardingBanner  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_banner_is_visible_initially(qapp) -> None:
    banner = OnboardingBanner()
    banner.show()
    assert banner.isVisible()


def test_banner_dismiss_hides_and_emits_signal(qapp) -> None:
    banner = OnboardingBanner()
    banner.show()
    fired: list[bool] = []
    banner.dismissed.connect(lambda: fired.append(True))
    banner.dismiss()
    assert not banner.isVisible()
    assert fired == [True]


def test_banner_dismiss_is_idempotent(qapp) -> None:
    banner = OnboardingBanner()
    banner.show()
    fired: list[bool] = []
    banner.dismissed.connect(lambda: fired.append(True))
    banner.dismiss()
    banner.dismiss()  # second call should not re-fire
    assert fired == [True]
