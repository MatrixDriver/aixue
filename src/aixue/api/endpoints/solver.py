"""解题 API 端点。"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from aixue.config import Settings
from aixue.db.session import get_db
from aixue.dependencies import get_current_user
from aixue.models.session import SolvingSession
from aixue.models.user import User
from aixue.schemas.session import (
    DetectResponse,
    FollowUpResponse,
    QuestionInfo,
    SessionDetail,
    SessionSummary,
    SolveResponse,
)
from aixue.services.llm_service import LLMService
from aixue.services.ocr_service import OCRService
from aixue.services.solver_service import SolverService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["解题"])

settings = Settings()


def _user_profile(user: User) -> dict:
    """从 User 模型构造解题所需的 profile 字典。"""
    return {
        "id": user.id,
        "name": user.name,
        "grade": user.grade,
        "subjects": user.subjects,
    }


@router.post("/detect", response_model=DetectResponse)
async def detect_questions(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> DetectResponse:
    """检测图片中的题目数量和完整性。"""
    image_data = await image.read()
    if len(image_data) > settings.max_image_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"图片大小超过限制({settings.max_image_size // 1024 // 1024}MB)",
        )
    media_type = image.content_type or "image/png"

    llm = LLMService()
    ocr = OCRService(llm)
    try:
        result = await ocr.detect_questions(image_data, media_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e

    questions = result.get("questions", [])
    question_count = result.get("question_count", len(questions))

    # 限制最多 5 题
    if question_count > 5:
        questions = questions[:5]
        msg = f"检测到 {question_count} 道题目，最多同时处理 5 道，建议分批拍照"
    elif question_count == 0:
        msg = "未检测到完整题目，请重新拍照确保题目完整"
    else:
        complete_count = sum(1 for q in questions if q.get("complete", False))
        incomplete = [q.get("label", str(q.get("index", ""))) for q in questions if not q.get("complete", False)]
        if complete_count == 0:
            msg = "检测到的题目均不完整，请重新拍照确保题目完整"
        elif incomplete:
            incomplete_str = "、".join(f"第{l}题" for l in incomplete)
            msg = f"检测到 {question_count} 道题目，其中{incomplete_str}不完整无法解答，请选择要解答的题目"
        else:
            msg = f"检测到 {question_count} 道题目，请选择要解答的题目"

    return DetectResponse(
        question_count=question_count,
        questions=[QuestionInfo(**q) for q in questions],
        message=msg,
    )


@router.post("/solve", response_model=SolveResponse)
async def solve_problem(
    image: UploadFile | None = File(None),
    text: str | None = Form(None),
    subject: str | None = Form(None),
    mode: str = Form("socratic"),
    session_id: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SolveResponse:
    """上传题目并获取解答。

    支持图片上传或文字输入，二者至少提供一个。
    """
    logger.info(
        "solve_problem 收到请求: image=%s, text=%s, subject=%s, mode=%s",
        f"{image.filename}({image.content_type})" if image else None,
        text[:50] if text else None,
        subject,
        mode,
    )

    if image is None and text is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供题目图片或文字",
        )

    # 读取图片数据
    image_data: bytes | None = None
    media_type: str | None = None
    if image is not None:
        image_data = await image.read()
        logger.info("图片数据读取成功: %d bytes", len(image_data))
        if len(image_data) > settings.max_image_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"图片大小超过限制({settings.max_image_size // 1024 // 1024}MB)",
            )
        media_type = image.content_type or "image/png"

    solver = SolverService()
    try:
        result = await solver.solve(
            image=image_data,
            media_type=media_type,
            text=text,
            subject=subject,
            mode=mode,
            session_id=session_id,
            user_profile=_user_profile(current_user),
            db=db,
        )
    except ValueError as e:
        logger.warning("解题服务异常: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e

    if "error" in result and result["error"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["error"],
        )

    return SolveResponse(**result)


@router.post("/solve/{session_id}/follow-up", response_model=FollowUpResponse)
async def follow_up(
    session_id: str,
    message: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FollowUpResponse:
    """多轮追问。"""
    solver = SolverService()
    try:
        result = await solver.follow_up(
            session_id=session_id,
            message_text=message,
            user_profile=_user_profile(current_user),
            db=db,
        )
    except ValueError as e:
        logger.warning("追问服务异常: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e

    if "error" in result and result["error"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )

    return FollowUpResponse(**result)


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    subject: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[SessionSummary]:
    """解题历史列表。"""
    query = (
        select(SolvingSession)
        .where(SolvingSession.user_id == current_user.id)
        .order_by(SolvingSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if subject:
        query = query.where(SolvingSession.subject == subject)

    result = await db.execute(query)
    sessions = result.scalars().all()
    return [SessionSummary.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetail:
    """获取完整对话记录。"""
    result = await db.execute(
        select(SolvingSession)
        .options(selectinload(SolvingSession.messages))
        .where(
            SolvingSession.id == session_id,
            SolvingSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    return SessionDetail.model_validate(session)
