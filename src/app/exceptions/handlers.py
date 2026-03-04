"""グローバル例外ハンドラ."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.not_found import NotFoundError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """アプリケーションにグローバル例外ハンドラを登録."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(
        request: Request,
        exc: NotFoundError,
    ) -> JSONResponse:
        logger.warning(
            "Not found | %s %s | field=%s value=%r",
            request.method,
            request.url,
            exc.field,
            exc.value,
        )
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )
