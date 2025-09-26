"""
Support Service for Telegram Bot

Handles support ticket creation and sending to support group.
Provides functionality to collect user messages, context, and conversation history
and send them to a designated support group with proper formatting.
"""

import json
import logging
import html
from datetime import datetime
from typing import Dict, Any, Optional, List
from telegram import Update, Bot
from telegram.error import TelegramError
from telegram.constants import ParseMode

from config import Config
from services.context_store import InMemoryUserContextStore


class SupportService:
    """Service for handling support requests and ticket creation"""
    
    def __init__(self, context_store: InMemoryUserContextStore):
        """Initialize support service with context store"""
        self.logger = logging.getLogger(__name__)
        self.context_store = context_store
        self.support_group_id = Config.SUPPORT_GROUP_ID
        self.support_thread_id = Config.SUPPORT_THREAD_ID
        
    def create_support_ticket(self, update: Update, user_message: str) -> Dict[str, Any]:
        """
        Create a support ticket with user information, context, and conversation history
        
        Args:
            update: Telegram update object
            user_message: User's support message
            
        Returns:
            Dictionary containing ticket data
        """
        user = update.effective_user
        chat = update.effective_chat
        
        # Get user context
        user_context = self.context_store.get_user_context(user.id)
        
        # Create ticket metadata
        ticket_meta = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "chat_id": chat.id,
            "chat_type": chat.type,
            "timestamp": datetime.now().isoformat(),
            "message_id": update.message.message_id if update.message else None
        }
        
        # Prepare user message (truncate if too long)
        truncated_message = user_message[:1000] if len(user_message) > 1000 else user_message
        
        # Get conversation history (last 10 messages)
        conversation_history = user_context.get("conversation_history", [])
        
        # Create context summary
        context_summary = self._create_context_summary(user_context)
        
        # Create full ticket
        ticket = {
            "meta": ticket_meta,
            "user_message": truncated_message,
            "context": context_summary,
            "conversation_history": conversation_history,
            "full_user_message": user_message  # Keep full message for JSON
        }
        
        return ticket
    
    def _create_context_summary(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of user context for support ticket"""
        return {
            "last_assets": user_context.get("last_assets", []),
            "last_analysis_type": user_context.get("last_analysis_type"),
            "last_period": user_context.get("last_period"),
            "portfolio_count": user_context.get("portfolio_count", 0),
            "saved_portfolios_count": len(user_context.get("saved_portfolios", {})),
            "analyzed_tickers": user_context.get("analyzed_tickers", []),
            "current_symbols": user_context.get("current_symbols", []),
            "current_currency": user_context.get("current_currency"),
            "active_reply_keyboard": user_context.get("active_reply_keyboard"),
            "preferences": user_context.get("preferences", {})
        }
    
    def format_support_message(self, ticket: Dict[str, Any]) -> str:
        """
        Format support ticket into a readable message for the support group
        
        Args:
            ticket: Support ticket data
            
        Returns:
            Formatted message string
        """
        meta = ticket["meta"]
        user_message = ticket["user_message"]
        context = ticket["context"]
        
        # Format user info
        user_info = f"👤 <b>Пользователь:</b> {meta['first_name']}"
        if meta.get('last_name'):
            user_info += f" {meta['last_name']}"
        if meta.get('username'):
            user_info += f" (@{meta['username']})"
        user_info += f"\n🆔 <b>ID:</b> {meta['user_id']}"
        user_info += f"\n💬 <b>Чат:</b> {meta['chat_id']} ({meta['chat_type']})"
        user_info += f"\n⏰ <b>Время:</b> {meta['timestamp']}"
        
        # Format context info
        context_info = "📊 <b>Контекст:</b>\n"
        if context.get('last_assets'):
            context_info += f"• Последние активы: {', '.join(context['last_assets'][:3])}\n"
        if context.get('last_analysis_type'):
            context_info += f"• Последний анализ: {context['last_analysis_type']}\n"
        if context.get('portfolio_count', 0) > 0:
            context_info += f"• Портфелей создано: {context['portfolio_count']}\n"
        if context.get('analyzed_tickers'):
            context_info += f"• Проанализировано тикеров: {len(context['analyzed_tickers'])}\n"
        
        # Format user message
        message_text = f"💬 <b>Сообщение:</b>\n{html.escape(user_message)}"
        
        # Combine all parts
        full_message = f"{user_info}\n\n{context_info}\n{message_text}"
        
        return full_message
    
    async def send_support_ticket(self, bot: Bot, ticket: Dict[str, Any]) -> bool:
        """
        Send support ticket to the support group
        
        Args:
            bot: Telegram bot instance
            ticket: Support ticket data
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Format the main message
            message_text = self.format_support_message(ticket)
            
            # Send main message to support group
            message_params = {
                "chat_id": self.support_group_id,
                "text": message_text,
                "parse_mode": ParseMode.HTML
            }
            
            # Add thread ID if specified
            if self.support_thread_id:
                message_params["message_thread_id"] = self.support_thread_id
            
            sent_message = await bot.send_message(**message_params)
            
            # If message is too long, send JSON as document
            if len(message_text) > Config.MAX_MESSAGE_LENGTH:
                await self._send_ticket_json(bot, ticket, sent_message.message_id)
            
            self.logger.info(f"Support ticket sent successfully for user {ticket['meta']['user_id']}")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Failed to send support ticket: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending support ticket: {e}")
            return False
    
    async def _send_ticket_json(self, bot: Bot, ticket: Dict[str, Any], reply_to_message_id: int) -> None:
        """Send full ticket data as JSON document"""
        try:
            # Create JSON content
            json_content = json.dumps(ticket, ensure_ascii=False, indent=2)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"support_ticket_{ticket['meta']['user_id']}_{timestamp}.json"
            
            # Send as document
            document_params = {
                "chat_id": self.support_group_id,
                "document": json_content.encode('utf-8'),
                "filename": filename,
                "caption": f"📄 Полные данные тикета для пользователя {ticket['meta']['user_id']}",
                "reply_to_message_id": reply_to_message_id
            }
            
            if self.support_thread_id:
                document_params["message_thread_id"] = self.support_thread_id
            
            await bot.send_document(**document_params)
            
        except Exception as e:
            self.logger.error(f"Failed to send ticket JSON: {e}")
    
    async def send_error_report(self, bot: Bot, error: Exception, context: Dict[str, Any] = None) -> bool:
        """
        Send error report to support group
        
        Args:
            bot: Telegram bot instance
            error: Exception that occurred
            context: Additional context information
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create error report
            error_report = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Format error message
            error_message = f"🚨 <b>Ошибка бота</b>\n\n"
            error_message += f"<b>Тип:</b> {error_report['error_type']}\n"
            error_message += f"<b>Сообщение:</b> {html.escape(str(error))}\n"
            error_message += f"<b>Время:</b> {error_report['timestamp']}\n"
            
            if context:
                error_message += f"\n<b>Контекст:</b>\n"
                for key, value in context.items():
                    error_message += f"• {key}: {html.escape(str(value))}\n"
            
            # Send error report
            message_params = {
                "chat_id": self.support_group_id,
                "text": error_message,
                "parse_mode": ParseMode.HTML
            }
            
            if self.support_thread_id:
                message_params["message_thread_id"] = self.support_thread_id
            
            await bot.send_message(**message_params)
            
            # Send full error report as JSON if context is large
            if context and len(str(context)) > 1000:
                await self._send_error_json(bot, error_report)
            
            self.logger.info(f"Error report sent successfully: {type(error).__name__}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send error report: {e}")
            return False
    
    async def _send_error_json(self, bot: Bot, error_report: Dict[str, Any]) -> None:
        """Send full error report as JSON document"""
        try:
            # Create JSON content
            json_content = json.dumps(error_report, ensure_ascii=False, indent=2)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_report_{timestamp}.json"
            
            # Send as document
            document_params = {
                "chat_id": self.support_group_id,
                "document": json_content.encode('utf-8'),
                "filename": filename,
                "caption": f"📄 Полный отчет об ошибке: {error_report['error_type']}"
            }
            
            if self.support_thread_id:
                document_params["message_thread_id"] = self.support_thread_id
            
            await bot.send_document(**document_params)
            
        except Exception as e:
            self.logger.error(f"Failed to send error JSON: {e}")
