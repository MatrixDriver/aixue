"""题库管理 API 端点。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aixue.db.session import get_db
from aixue.dependencies import get_current_user
from aixue.models.user import User
from aixue.schemas.problem import GenerateRequest, GenerateResponse, ProblemOut
from aixue.services.problem_service import ProblemService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/problems", tags=["题库"])


@router.get("", response_model=list[ProblemOut])
async def list_problems(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    subject: str | None = Query(None),
    grade_level: str | None = Query(None),
    difficulty: int | None = Query(None, ge=1, le=5),
    knowledge_point: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[ProblemOut]:
    """查询题目列表，支持按学科、难度、知识点筛选。"""
    service = ProblemService()
    problems = await service.list_problems(
        db=db,
        subject=subject,
        grade_level=grade_level,
        difficulty=difficulty,
        knowledge_point=knowledge_point,
        limit=limit,
        offset=offset,
    )
    return [ProblemOut.model_validate(p) for p in problems]


@router.get("/{problem_id}", response_model=ProblemOut)
async def get_problem(
    problem_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProblemOut:
    """获取题目详情。"""
    service = ProblemService()
    problem = await service.get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在",
        )
    return ProblemOut.model_validate(problem)


@router.post("/generate", response_model=GenerateResponse)
async def generate_variant(
    req: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    """LLM 生成变式题。"""
    service = ProblemService()
    result = await service.generate_variant(
        db=db,
        source_problem_id=req.source_problem_id,
        subject=req.subject,
        knowledge_points=req.knowledge_points,
        grade_level=req.grade_level,
        difficulty=req.difficulty,
    )

    if "error" in result:
        return GenerateResponse(error=result["error"], raw=result.get("raw"))

    return GenerateResponse(**result)
