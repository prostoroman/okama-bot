"""
Rate Limiter Module for Telegram Bot

This module implements token bucket rate limiting for both per-user and global limits.
Based on the provided code structure with improvements for integration.
"""

import os
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from telegram import Update
from telegram.ext import ContextTypes

# ========= ENV Configuration =========
# Per-user limits (targeting ~30/day softly)
DAILY_TARGET = float(os.getenv("DAILY_TARGET", "30"))  # average target per day
BUCKET_CAPACITY = float(os.getenv("BUCKET_CAPACITY", "10"))  # max burst per user
# refill rate from target/day:
REFILL_RATE_TPS = DAILY_TARGET / 86400.0  # tokens/sec (≈ 0.000347 for 30/day)

# Global anti-burst
GLOBAL_BUCKET_CAPACITY = float(os.getenv("GLOBAL_BUCKET_CAPACITY", "200"))
GLOBAL_REFILL_RATE_TPS = float(os.getenv("GLOBAL_REFILL_RATE_TPS", "10.0"))

# Messages
BLOCK_MESSAGE_USER = os.getenv("BLOCK_MESSAGE_USER", "Достигнут лимит запросов к боту. Подождите ~{wait:.1f} сек.")
BLOCK_MESSAGE_GLOBAL = os.getenv("BLOCK_MESSAGE_GLOBAL", "Сервис занят. Подождите ~{wait:.1f} сек.")

# ========= Token Bucket Implementation =========
@dataclass
class _Bucket:
    """Internal bucket data structure"""
    tokens: float
    last_refill: float

class TokenBucketSingle:
    """
    Single bucket (global).
    capacity: max tokens (burst)
    refill_rate: tokens per second (average bandwidth)
    """
    
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self._b = _Bucket(tokens=self.capacity, last_refill=time.monotonic())
        self._lock = asyncio.Lock()

    async def allow(self, cost: float = 1.0) -> Tuple[bool, float]:
        """
        Check if request is allowed and consume tokens if so.
        
        Args:
            cost: Number of tokens to consume
            
        Returns:
            Tuple of (allowed, wait_seconds_if_denied)
        """
        now = time.monotonic()
        async with self._lock:
            elapsed = max(0.0, now - self._b.last_refill)
            if elapsed > 0:
                self._b.tokens = min(self.capacity, self._b.tokens + elapsed * self.refill_rate)
                self._b.last_refill = now

            if self._b.tokens >= cost:
                self._b.tokens -= cost
                return True, 0.0

            deficit = cost - self._b.tokens
            wait = float("inf") if self.refill_rate <= 0 else deficit / self.refill_rate
            return False, wait

    async def status(self) -> Tuple[float, float]:
        """
        Get current bucket status.
        
        Returns:
            Tuple of (current_tokens, refill_rate)
        """
        now = time.monotonic()
        async with self._lock:
            elapsed = max(0.0, now - self._b.last_refill)
            if elapsed > 0:
                self._b.tokens = min(self.capacity, self._b.tokens + elapsed * self.refill_rate)
                self._b.last_refill = now
            return self._b.tokens, self.refill_rate

class TokenBucketsPerUser:
    """
    Bucket per user (by user_id).
    Same capacity/refill_rate for all users.
    """
    
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self._buckets: Dict[int, _Bucket] = {}
        self._lock = asyncio.Lock()

    async def allow(self, user_id: int, cost: float = 1.0) -> Tuple[bool, float]:
        """
        Check if user request is allowed and consume tokens if so.
        
        Args:
            user_id: Telegram user ID
            cost: Number of tokens to consume
            
        Returns:
            Tuple of (allowed, wait_seconds_if_denied)
        """
        now = time.monotonic()
        async with self._lock:
            b = self._buckets.get(user_id)
            if b is None:
                b = _Bucket(tokens=self.capacity, last_refill=now)
                self._buckets[user_id] = b

            elapsed = max(0.0, now - b.last_refill)
            if elapsed > 0:
                b.tokens = min(self.capacity, b.tokens + elapsed * self.refill_rate)
                b.last_refill = now

            if b.tokens >= cost:
                b.tokens -= cost
                return True, 0.0

            deficit = cost - b.tokens
            wait = float("inf") if self.refill_rate <= 0 else deficit / self.refill_rate
            return False, wait

    async def status(self, user_id: int) -> Tuple[float, float]:
        """
        Get user bucket status.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (current_tokens, refill_rate)
        """
        now = time.monotonic()
        async with self._lock:
            b = self._buckets.get(user_id)
            if b is None:
                # if user hasn't made requests yet, consider bucket full
                return self.capacity, self.refill_rate
            elapsed = max(0.0, now - b.last_refill)
            if elapsed > 0:
                b.tokens = min(self.capacity, b.tokens + elapsed * self.refill_rate)
                b.last_refill = now
            return b.tokens, self.refill_rate

    async def get_user_count(self) -> int:
        """Get number of active users with buckets"""
        async with self._lock:
            return len(self._buckets)

# ========= Rate Limiter Manager =========
class RateLimiter:
    """
    Main rate limiter class that manages both global and per-user limits.
    """
    
    def __init__(self):
        """Initialize rate limiter with configured limits"""
        self.global_bucket = TokenBucketSingle(GLOBAL_BUCKET_CAPACITY, GLOBAL_REFILL_RATE_TPS)
        self.user_buckets = TokenBucketsPerUser(BUCKET_CAPACITY, REFILL_RATE_TPS)
        
    async def check_rate_limit(self, user_id: int, cost: float = 1.0) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed for user.
        
        Args:
            user_id: Telegram user ID
            cost: Number of tokens to consume
            
        Returns:
            Tuple of (allowed, error_message_if_denied)
        """
        # 1) Check global bucket first
        allowed_g, wait_g = await self.global_bucket.allow(cost=cost)
        if not allowed_g:
            wait_time = wait_g if wait_g != float("inf") else 9999.0
            return False, BLOCK_MESSAGE_GLOBAL.format(wait=wait_time)

        # 2) Check per-user bucket
        allowed_u, wait_u = await self.user_buckets.allow(user_id, cost=cost)
        if not allowed_u:
            wait_time = wait_u if wait_u != float("inf") else 9999.0
            return False, BLOCK_MESSAGE_USER.format(wait=wait_time)

        return True, None

    async def get_status(self, user_id: int) -> Dict[str, any]:
        """
        Get current rate limit status for user and global.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with status information
        """
        u_tokens, u_rate = await self.user_buckets.status(user_id)
        g_tokens, g_rate = await self.global_bucket.status()
        user_count = await self.user_buckets.get_user_count()
        
        return {
            'user_tokens': u_tokens,
            'user_rate': u_rate,
            'global_tokens': g_tokens,
            'global_rate': g_rate,
            'active_users': user_count,
            'daily_target': DAILY_TARGET,
            'bucket_capacity': BUCKET_CAPACITY
        }

    def _fmt_num(self, x: float) -> str:
        """Format number for display"""
        return str(int(x)) if abs(x - int(x)) < 1e-9 else f"{x:.3f}"

    async def get_status_message(self, user_id: int) -> str:
        """
        Get formatted status message for user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Formatted status message
        """
        status = await self.get_status(user_id)
        
        per_user_msg = (
            f"Персональный лимит: {self._fmt_num(status['user_tokens'])}/{self._fmt_num(BUCKET_CAPACITY)} токенов, "
            f"пополнение {self._fmt_num(status['user_rate'])} ток/сек "
            f"(~{self._fmt_num(1/status['user_rate'])} сек на ток) — таргет ≈ {int(DAILY_TARGET)}/сутки."
        )
        
        global_msg = (
            f"Глобальный лимит: {self._fmt_num(status['global_tokens'])}/{self._fmt_num(GLOBAL_BUCKET_CAPACITY)} токенов, "
            f"пополнение {self._fmt_num(status['global_rate'])} ток/сек "
            f"(≈ {int(status['global_rate'])} rps). Активных пользователей: {status['active_users']}"
        )
        
        return f"Статус лимитов:\n• {per_user_msg}\n• {global_msg}"

# ========= Global Rate Limiter Instance =========
# Initialize global rate limiter instance
rate_limiter = RateLimiter()

# ========= Helper Functions =========
async def check_user_rate_limit(update: Update, context: ContextTypes.DEFAULT_TYPE, cost: float = 1.0) -> bool:
    """
    Check rate limit for user and send error message if exceeded.
    
    Args:
        update: Telegram update object
        context: Bot context
        cost: Number of tokens to consume
        
    Returns:
        True if request is allowed, False if rate limited
    """
    if not update or not update.effective_user:
        return False
        
    user_id = update.effective_user.id
    allowed, error_message = await rate_limiter.check_rate_limit(user_id, cost)
    
    if not allowed and error_message:
        await update.message.reply_text(error_message)
        return False
        
    return True

async def get_rate_limit_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """
    Get rate limit status message for user.
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        Formatted status message
    """
    if not update or not update.effective_user:
        return "Ошибка: не удалось определить пользователя"
        
    user_id = update.effective_user.id
    return await rate_limiter.get_status_message(user_id)