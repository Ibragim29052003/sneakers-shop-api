from typing import Any

 
from rest_framework.views import APIView

from core.permissions import IsAdminRole


class DebugSentryView(APIView):
    """Тестовый endpoint для проверки интеграции Sentry."""

    permission_classes = [IsAdminRole]

    def get(self, request: Any) -> Any:
        """Выполняет действие `get`."""
        raise RuntimeError('Sentry test exception from /api/v1/debug/sentry/')
