"""
Payment service for Telegram Stars integration
Handles Pro subscription purchases and payment processing
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from .db import upgrade_to_pro, get_user_status

logger = logging.getLogger(__name__)

# Payment configuration
PRO_PRICE_STARS = int(os.getenv('PRO_PRICE_STARS', '10'))  # Price in Telegram Stars
PRO_DURATION_DAYS = int(os.getenv('PRO_DURATION_DAYS', '30'))
STARS_TEST_MODE = os.getenv('STARS_TEST_MODE', 'false').lower() == 'true'

class PaymentService:
    """Service for handling payment operations"""
    
    def __init__(self, bot_instance=None):
        self.logger = logging.getLogger(__name__)
        self.bot_instance = bot_instance
        mode = "TEST" if STARS_TEST_MODE else "PRODUCTION"
        self.logger.info(f"Payment service initialized for Telegram Stars ({mode} mode)")
    
    async def send_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Send invoice for Pro subscription using Telegram Stars
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        user_status = get_user_status(user_id)
        
        # For active Pro users, show renewal invoice instead of blocking
        # This allows users to extend their subscription
        
        try:
            # Create invoice with empty provider_token for Telegram Stars
            await context.bot.send_invoice(
                chat_id=user_id,
                title="💎 Pro доступ к боту",
                description=f"Безлимитные запросы на {PRO_DURATION_DAYS} дней",
                payload=f"pro_subscription_{user_id}",
                provider_token="",  # Empty string for Telegram Stars
                currency="XTR",  # Telegram Stars currency code
                prices=[LabeledPrice("Pro доступ", PRO_PRICE_STARS)],
                start_parameter=f"pro_{user_id}",
                is_flexible=False,
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                send_phone_number_to_provider=False,
                send_email_to_provider=False,
                disable_notification=False,
                protect_content=False,
                reply_to_message_id=None,
                allow_sending_without_reply=False,
                reply_markup=None
            )
            
        except TelegramError as e:
            self.logger.error(f"Failed to send invoice to user {user_id}: {e}")
            error_message = "❌ Ошибка при создании счета. Попробуйте позже или обратитесь к поддержке."
            
            # Handle both regular messages and callback queries
            if update.message:
                await update.message.reply_text(error_message)
            elif update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(error_message)
            else:
                # Fallback: send message using context.bot
                chat_id = update.effective_chat.id
                await context.bot.send_message(chat_id, error_message)
    
    async def send_stars_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Send Stars payment request
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        user_status = get_user_status(user_id)
        
        # Check if user already has active Pro subscription
        if user_status['is_pro_active']:
            paid_until = datetime.fromisoformat(user_status['paid_until'])
            new_expiry = paid_until + timedelta(days=PRO_DURATION_DAYS)
            
            message = f"""🔄 <b>Продление Pro подписки</b>

<b>Текущая подписка:</b> до {paid_until.strftime('%d.%m.%Y')}
<b>После продления:</b> до {new_expiry.strftime('%d.%m.%Y')}

<b>Что включено:</b>
✅ Безлимитные запросы к боту
✅ Приоритетная поддержка
✅ Расширенные функции анализа
✅ Доступ к новым возможностям
✅ Дополнительно {PRO_DURATION_DAYS} дней

<b>Оплата через Telegram Stars</b>
{f"🧪 <b>ТЕСТОВЫЙ РЕЖИМ</b> - используйте тестовые Stars" if STARS_TEST_MODE else ""}
Нажмите кнопку ниже для продления:"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🔄 Продлить на {PRO_DURATION_DAYS} дней - {PRO_PRICE_STARS} ⭐", callback_data="pay_stars")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_payment")]
            ])
            
            # Handle both regular messages and callback queries
            if update.message:
                await update.message.reply_text(message, reply_markup=keyboard, parse_mode='HTML')
            elif update.callback_query and update.callback_query.message:
                await update.callback_query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            else:
                # Fallback: send message using context.bot
                chat_id = update.effective_chat.id
                await context.bot.send_message(chat_id, message, reply_markup=keyboard, parse_mode='HTML')
            return
        
        message = f"""💎 <b>Pro доступ - {PRO_PRICE_STARS} ⭐</b>

<b>Что включено:</b>
✅ Безлимитные запросы к боту
✅ Приоритетная поддержка
✅ Расширенные функции анализа
✅ Доступ к новым возможностям
✅ Действует {PRO_DURATION_DAYS} дней

<b>Оплата через Telegram Stars</b>
{f"🧪 <b>ТЕСТОВЫЙ РЕЖИМ</b> - используйте тестовые Stars" if STARS_TEST_MODE else ""}
Нажмите кнопку ниже для покупки:"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"💎 Оплатить {PRO_PRICE_STARS} ⭐", callback_data="pay_stars")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_payment")]
        ])
        
        # Handle both regular messages and callback queries
        if update.message:
            await update.message.reply_text(message, reply_markup=keyboard, parse_mode='HTML')
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text(message, reply_markup=keyboard, parse_mode='HTML')
        else:
            # Fallback: send message using context.bot
            chat_id = update.effective_chat.id
            await context.bot.send_message(chat_id, message, reply_markup=keyboard, parse_mode='HTML')
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle successful payment and upgrade user to Pro
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        if not update.message or not update.message.successful_payment:
            return
        
        user_id = update.effective_user.id
        payment = update.message.successful_payment
        
        # Verify payment details
        if payment.total_amount != PRO_PRICE_STARS:
            self.logger.warning(f"Payment amount mismatch for user {user_id}: {payment.total_amount} != {PRO_PRICE_STARS}")
        
        # Check if user already has active Pro subscription for renewal
        user_status = get_user_status(user_id)
        
        if user_status['is_pro_active']:
            # Extend existing subscription
            current_paid_until = datetime.fromisoformat(user_status['paid_until'])
            new_paid_until = current_paid_until + timedelta(days=PRO_DURATION_DAYS)
            
            # Update subscription in database
            success = upgrade_to_pro(user_id, PRO_DURATION_DAYS)
            
            if success:
                message = f"""🎉 <b>Продление успешно!</b>

✅ Ваша Pro подписка продлена
📅 Действует до: {new_paid_until.strftime('%d.%m.%Y')}
💎 Спасибо за продление!

Теперь у вас безлимитный доступ ко всем функциям бота.

Используйте /profile для просмотра статуса."""
                
                await update.message.reply_text(message, parse_mode='HTML')
                
                # Log successful renewal
                self.logger.info(f"User {user_id} successfully renewed Pro subscription until {new_paid_until.isoformat()}")
            else:
                await update.message.reply_text(
                    "❌ Ошибка при продлении Pro доступа. Обратитесь к поддержке."
                )
                self.logger.error(f"Failed to renew Pro subscription for user {user_id}")
        else:
            # Upgrade new user to Pro
            success = upgrade_to_pro(user_id, PRO_DURATION_DAYS)
            
            if success:
                paid_until = datetime.utcnow().replace(microsecond=0) + timedelta(days=PRO_DURATION_DAYS)
                
                message = f"""🎉 <b>Оплата успешна!</b>

✅ Ваш Pro доступ активирован
📅 Действует до: {paid_until.strftime('%d.%m.%Y')}
💎 Спасибо за покупку!

Теперь у вас безлимитный доступ ко всем функциям бота.

Используйте /profile для просмотра статуса."""
                
                await update.message.reply_text(message, parse_mode='HTML')
                
                # Log successful payment
                self.logger.info(f"User {user_id} successfully upgraded to Pro until {paid_until.isoformat()}")
                
            else:
                await update.message.reply_text(
                    "❌ Ошибка при активации Pro доступа. Обратитесь к поддержке."
                )
                self.logger.error(f"Failed to upgrade user {user_id} to Pro after payment")
    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle pre-checkout query for invoice payments
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        query = update.pre_checkout_query
        
        # Verify payment details
        if query.total_amount != PRO_PRICE_STARS:
            await query.answer(ok=False, error_message="Неверная сумма платежа")
            return
        
        # Verify payload
        expected_payload = f"pro_subscription_{query.from_user.id}"
        if query.invoice_payload != expected_payload:
            await query.answer(ok=False, error_message="Неверные данные платежа")
            return
        
        # Approve payment
        await query.answer(ok=True)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle callback queries for payment buttons
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            query = update.callback_query
            if not query:
                self.logger.error("No callback query found in update")
                return
                
            await query.answer()
            
            if query.data == "buy_pro":
                await self.send_stars_payment(update, context)
            elif query.data == "pay_stars":
                await self.send_invoice(update, context)
            elif query.data == "cancel_payment":
                await self._redirect_to_start(update, context)
            elif query.data == "show_profile":
                await self.show_profile(update, context)
            else:
                self.logger.warning(f"Unknown payment callback: {query.data}")
                
        except Exception as e:
            self.logger.error(f"Error handling payment callback: {e}")
            # Try to send error message
            try:
                if update.callback_query and update.callback_query.message:
                    chat_id = update.callback_query.message.chat_id
                    await context.bot.send_message(chat_id, f"❌ Ошибка при обработке кнопки: {str(e)}")
            except Exception as fallback_error:
                self.logger.error(f"Failed to send error message: {fallback_error}")
    
    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Show user profile with subscription status
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        user_status = get_user_status(user_id)
        
        # Format user info
        username = update.effective_user.username or "Не указан"
        first_name = update.effective_user.first_name or ""
        last_name = update.effective_user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        
        # Format subscription info
        if user_status['is_pro_active']:
            paid_until = datetime.fromisoformat(user_status['paid_until'])
            plan_info = f"💎 <b>Pro</b> (до {paid_until.strftime('%d.%m.%Y')})"
            requests_info = "♾️ Безлимитные запросы"
            button_text = "🔄 Продлить Pro"
        else:
            plan_info = "🆓 <b>Бесплатный</b>"
            remaining = user_status['remaining_requests']
            total = user_status['daily_limit']
            requests_info = f"📊 {remaining}/{total} запросов сегодня"
            button_text = "💎 Купить Pro"
        
        # Add timestamp to make message unique and avoid "Message is not modified" error
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"""👤 <b>Профиль пользователя</b>

<b>Имя:</b> {full_name}
<b>Username:</b> @{username}
<b>ID:</b> {user_id}

<b>Подписка:</b> {plan_info}
<b>Запросы:</b> {requests_info}

/support - Поддержка

<i>Обновлено: {timestamp}</i>"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(button_text, callback_data="buy_pro")]
        ])
        
        try:
            if update.callback_query and update.callback_query.message:
                # Try to edit the existing message
                await update.callback_query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            elif update.message:
                # Send new message
                await update.message.reply_text(message, reply_markup=keyboard, parse_mode='HTML')
            else:
                # Fallback: send message using context.bot
                chat_id = update.effective_chat.id
                await context.bot.send_message(chat_id, message, reply_markup=keyboard, parse_mode='HTML')
        except Exception as e:
            # If editing fails (e.g., "Message is not modified"), send a new message
            try:
                chat_id = update.effective_chat.id
                await context.bot.send_message(chat_id, message, reply_markup=keyboard, parse_mode='HTML')
            except Exception as fallback_error:
                # Last resort: send without markup
                chat_id = update.effective_chat.id
                await context.bot.send_message(chat_id, message, parse_mode='HTML')
    
    async def _redirect_to_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Redirect user to start command after canceling payment
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            # Call the actual start_command method if bot instance is available
            if self.bot_instance:
                await self.bot_instance.start_command(update, context)
            else:
                # Fallback: send a simple message
                if update.callback_query and update.callback_query.message:
                    await update.callback_query.edit_message_text("Покупка отменена. Используйте /start для возврата в главное меню.")
                else:
                    chat_id = update.effective_chat.id
                    await context.bot.send_message(chat_id, "Покупка отменена. Используйте /start для возврата в главное меню.")
            
        except Exception as e:
            self.logger.error(f"Error redirecting to start command: {e}")
            # Fallback: send a simple message
            try:
                if update.callback_query and update.callback_query.message:
                    await update.callback_query.edit_message_text("Покупка отменена. Используйте /start для возврата в главное меню.")
                else:
                    chat_id = update.effective_chat.id
                    await context.bot.send_message(chat_id, "Покупка отменена. Используйте /start для возврата в главное меню.")
            except Exception as fallback_error:
                self.logger.error(f"Failed to send fallback message: {fallback_error}")

# Global payment service instance (will be initialized with bot instance)
payment_service = None
