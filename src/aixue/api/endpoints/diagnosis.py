"""学情诊断 API 端点。"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aixue.db.session import get_db
from aixue.dependencies import get_current_user
from aixue.models.diagnosis import DiagnosticReport
from aixue.models.user import User
from aixue.schemas.diagnosis import (
    DiagnosisReportDetail,
    DiagnosisReportSummary,
    DiagnosisResponse,
    ExamImportResponse,
)
from aixue.services.diagnosis_service import DiagnosisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnosis", tags=["学情诊断"])


@router.post("/analyze", response_model=DiagnosisResponse)
async def run_diagnosis(
    scope: str = Form("full"),
    subject: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiagnosisResponse:
    """运行学情诊断分析。"""
    service = DiagnosisService()
    result = await service.analyze(
        user_id=current_user.id,
        scope=scope,
        subject=subject,
        db=db,
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["error"],
        )

    return DiagnosisResponse(**result)


@router.post("/import-exam", response_model=ExamImportResponse)
async def import_exam(
    images: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamImportResponse:
    """上传试卷进行识别和导入。"""
    image_list: list[tuple[bytes, str]] = []
    for img in images:
        data = await img.read()
        media_type = img.content_type or "image/png"
        image_list.append((data, media_type))

    service = DiagnosisService()
    result = await service.import_exam(
        user_id=current_user.id,
        images=image_list,
        db=db,
    )

    return ExamImportResponse(**result)


@router.get("/reports", response_model=list[DiagnosisReportSummary])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DiagnosisReportSummary]:
    """获取诊断报告列表。"""
    result = await db.execute(
        select(DiagnosticReport)
        .where(DiagnosticReport.user_id == current_user.id)
        .order_by(DiagnosticReport.created_at.desc())
    )
    reports = result.scalars().all()
    return [DiagnosisReportSummary.model_validate(r) for r in reports]


@router.get("/reports/{report_id}", response_model=DiagnosisReportDetail)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiagnosisReportDetail:
    """获取诊断报告详情。"""
    result = await db.execute(
        select(DiagnosticReport).where(
            DiagnosticReport.id == report_id,
            DiagnosticReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在",
        )

    return DiagnosisReportDetail.model_validate(report)
