"""
Botality Analytics Service
Интеграция с Botality API для аналитики Telegram бота
"""

import asyncio
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
import threading

logger = logging.getLogger(__name__)


class BotalityService:
    """Сервис для отправки аналитики в Botality"""
    
    def __init__(self, token: str):
        """
        Инициализация сервиса Botality
        
        Args:
            token: Токен для аутентификации в Botality API
        """
        self.token = token
        self.api_url = "https://botality.cc/api/v1/messages"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
<<<<<<< HEAD
        self.timeout = 10
=======
        self.session.timeout = 10
>>>>>>> origin/main
    
    def send_message_analytics_sync(self, message_data: Dict[str, Any]) -> bool:
        """
        Синхронная отправка аналитики сообщения в Botality
        
        Args:
            message_data: Данные сообщения для аналитики
            
        Returns:
            bool: True если успешно отправлено, False в противном случае
        """
        try:
            payload = {
                "token": self.token,
                "data": message_data
            }
            
<<<<<<< HEAD
            response = self.session.post(self.api_url, json=payload, timeout=self.timeout)
=======
            response = self.session.post(self.api_url, json=payload)
>>>>>>> origin/main
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok":
                    logger.debug("Botality analytics sent successfully")
                    return True
                else:
                    logger.warning(f"Botality API returned non-ok status: {result}")
                    return False
            else:
                logger.warning(f"Botality API returned status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning("Botality API request timeout")
            return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Botality API request error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Botality analytics: {e}")
            return False
    
    async def send_message_analytics(self, message_data: Dict[str, Any]) -> bool:
        """
        Асинхронная отправка аналитики сообщения в Botality
        
        Args:
            message_data: Данные сообщения для аналитики
            
        Returns:
            bool: True если успешно отправлено, False в противном случае
        """
        # Запускаем синхронную отправку в отдельном потоке
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_message_analytics_sync, message_data)
    
    def prepare_message_data(self, update) -> Dict[str, Any]:
        """
        Подготовка данных сообщения для отправки в Botality
        
        Args:
            update: Telegram Update объект
            
        Returns:
            Dict с данными сообщения
        """
        try:
            message = update.message
            if not message:
                return {}
                
            from_user = message.from_user
            
            message_data = {
                "message_id": message.message_id,
                "from": {
                    "id": from_user.id,
                    "is_bot": from_user.is_bot,
                },
                "date": int(message.date.timestamp()),
                "text": message.text or ""
            }
            
            # Добавляем username если есть
            if from_user.username:
                message_data["from"]["username"] = from_user.username
                
            return message_data
            
        except Exception as e:
            logger.error(f"Error preparing Botality message data: {e}")
            return {}
    
    async def send_analytics_async(self, update) -> None:
        """
        Асинхронная отправка аналитики (неблокирующая)
        
        Args:
            update: Telegram Update объект
        """
        try:
            message_data = self.prepare_message_data(update)
            if not message_data:
                return
                
            # Создаем задачу для асинхронной отправки
            asyncio.create_task(self.send_message_analytics(message_data))
            
        except Exception as e:
            logger.error(f"Error in async Botality analytics: {e}")


# Глобальный экземпляр сервиса (будет инициализирован в config.py)
botality_service: Optional[BotalityService] = None


def get_botality_service() -> Optional[BotalityService]:
    """Получение глобального экземпляра Botality сервиса"""
    return botality_service


def initialize_botality_service(token: str) -> None:
    """
    Инициализация глобального Botality сервиса
    
    Args:
        token: Токен для Botality API
    """
    global botality_service
    if token:
        botality_service = BotalityService(token)
        logger.info("Botality service initialized")
    else:
        logger.warning("Botality token not provided, analytics disabled")


async def send_botality_analytics(update) -> None:
    """
    Удобная функция для отправки аналитики в Botality
    
    Args:
        update: Telegram Update объект
    """
    service = get_botality_service()
    if service:
        await service.send_analytics_async(update)
    else:
        logger.debug("Botality service not available")
