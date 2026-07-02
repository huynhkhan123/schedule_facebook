from pathlib import Path
from typing import Protocol

from facebook_group_tool.application.dto import ComposerResult, SafetyDetection, SyncedGroupInput


class BrowserSessionPort(Protocol):
    async def open(self) -> None: ...
    async def close(self) -> None: ...
    async def goto(self, url: str) -> None: ...


class GroupSyncPort(Protocol):
    async def collect_visible_groups(self) -> list[SyncedGroupInput]: ...


class PostComposerPort(Protocol):
    async def prepare_post(
        self,
        target_url: str,
        body_text: str,
        media_paths: list[Path],
    ) -> ComposerResult: ...
    async def publish_prepared_post(self) -> ComposerResult: ...


class CheckpointDetectorPort(Protocol):
    async def detect(self) -> SafetyDetection: ...
