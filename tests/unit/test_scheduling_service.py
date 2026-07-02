from facebook_group_tool.application.services.scheduling_service import SchedulingService


def test_delay_sequence_uses_bounds_deterministically() -> None:
    service = SchedulingService()

    delays = service.build_delay_sequence(
        target_count=3,
        min_delay_seconds=300,
        max_delay_seconds=900,
    )

    assert delays == (300, 600, 900)
