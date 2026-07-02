from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyPolicy:
    global_daily_auto_limit: int = 20
    min_delay_seconds: int = 300
    max_delay_seconds: int = 900

    def __post_init__(self) -> None:
        if self.global_daily_auto_limit > 20:
            raise ValueError("global_daily_auto_limit cannot exceed 20")
        if self.global_daily_auto_limit < 1:
            raise ValueError("global_daily_auto_limit must be at least 1")
        if self.min_delay_seconds < 300:
            raise ValueError("min_delay_seconds must be at least 300")
        if self.min_delay_seconds > self.max_delay_seconds:
            raise ValueError("min_delay_seconds must be <= max_delay_seconds")
