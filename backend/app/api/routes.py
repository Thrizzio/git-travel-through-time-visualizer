from fastapi import APIRouter

from . import export, metrics, prediction, repository


router = APIRouter()

router.include_router(repository.router)
router.include_router(metrics.router)
router.include_router(prediction.router)
router.include_router(export.router)
