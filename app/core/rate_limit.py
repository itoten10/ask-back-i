from collections import defaultdict
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.security import now_utc


class RateLimiter:
    """メモリベースのレート制限（デモ用）"""
    
    def __init__(self):
        self._attempts: dict[str, list[datetime]] = defaultdict(list)
    
    def check_rate_limit(self, email: str) -> bool:
        """レート制限チェック（True: 許可、False: 制限超過）"""
        if not settings.rate_limit_enabled:
            return True
        
        now = now_utc()
        window_start = now - timedelta(minutes=settings.rate_limit_window_minutes)
        
        # 古い試行を削除
        self._attempts[email] = [
            attempt_time
            for attempt_time in self._attempts[email]
            if attempt_time > window_start
        ]
        
        # 試行回数チェック
        if len(self._attempts[email]) >= settings.rate_limit_max_attempts:
            return False
        
        # 新しい試行を記録
        self._attempts[email].append(now)
        return True
    
    def reset(self, email: str) -> None:
        """特定ユーザーのレート制限をリセット"""
        if email in self._attempts:
            del self._attempts[email]


# グローバルインスタンス
rate_limiter = RateLimiter()


