from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from facebook_group_tool.application.dto import CreateCampaignInput
from facebook_group_tool.application.services.safety_guard import SafetyViolation
from facebook_group_tool.application.use_cases.create_campaign import CreateCampaignUseCase
from facebook_group_tool.application.use_cases.pause_campaign import PauseCampaignUseCase
from facebook_group_tool.application.use_cases.resume_campaign import ResumeCampaignUseCase
from facebook_group_tool.domain.entities.campaign import Campaign
from facebook_group_tool.presentation.api.dependencies import (
    campaign_repository,
    get_create_campaign_use_case,
    get_pause_campaign_use_case,
    get_resume_campaign_use_case,
)
from facebook_group_tool.presentation.api.schemas.campaign_schema import (
    CampaignResponse,
    CreateCampaignRequest,
)

router = APIRouter()

CreateCampaignDependency = Annotated[CreateCampaignUseCase, Depends(get_create_campaign_use_case)]
PauseCampaignDependency = Annotated[PauseCampaignUseCase, Depends(get_pause_campaign_use_case)]
ResumeCampaignDependency = Annotated[ResumeCampaignUseCase, Depends(get_resume_campaign_use_case)]


def to_campaign_response(campaign: Campaign) -> CampaignResponse:
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        post_id=campaign.post_id,
        mode=campaign.mode,
        status=campaign.status.value,
        daily_auto_limit=campaign.daily_auto_limit,
        min_delay_seconds=campaign.min_delay_seconds,
        max_delay_seconds=campaign.max_delay_seconds,
    )


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CreateCampaignRequest,
    use_case: CreateCampaignDependency,
) -> CampaignResponse:
    try:
        campaign = await use_case.execute(
            CreateCampaignInput(
                name=request.name,
                post_id=request.post_id,
                mode=request.mode,
                target_group_ids=tuple(request.target_group_ids),
                daily_auto_limit=request.daily_auto_limit,
                min_delay_seconds=request.min_delay_seconds,
                max_delay_seconds=request.max_delay_seconds,
            ),
            dry_run_completed=True,
        )
    except SafetyViolation as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return to_campaign_response(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID) -> CampaignResponse:
    campaign = await campaign_repository.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return to_campaign_response(campaign)


@router.post("/{campaign_id}/dry-run")
async def dry_run_campaign(campaign_id: UUID) -> dict[str, str]:
    return {"status": "ok", "campaign_id": str(campaign_id)}


@router.post("/{campaign_id}/start")
async def start_campaign(campaign_id: UUID) -> dict[str, str]:
    return {"status": "started", "campaign_id": str(campaign_id)}


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    use_case: PauseCampaignDependency,
) -> CampaignResponse:
    campaign = await use_case.execute(campaign_id)
    return to_campaign_response(campaign)


@router.post("/{campaign_id}/resume", response_model=CampaignResponse)
async def resume_campaign(
    campaign_id: UUID,
    use_case: ResumeCampaignDependency,
) -> CampaignResponse:
    campaign = await use_case.execute(campaign_id)
    return to_campaign_response(campaign)


@router.post("/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: UUID) -> dict[str, str]:
    return {"status": "cancelled", "campaign_id": str(campaign_id)}


@router.get("/{campaign_id}/logs")
async def campaign_logs(campaign_id: UUID) -> list[dict[str, str]]:
    return []
