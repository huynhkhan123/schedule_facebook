class SchedulingService:
    def build_delay_sequence(
        self,
        *,
        target_count: int,
        min_delay_seconds: int,
        max_delay_seconds: int,
    ) -> tuple[int, ...]:
        if target_count <= 0:
            return ()
        if target_count == 1:
            return (min_delay_seconds,)
        step = (max_delay_seconds - min_delay_seconds) / (target_count - 1)
        return tuple(round(min_delay_seconds + (step * index)) for index in range(target_count))
