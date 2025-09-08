"""
Simple chart analysis service as fallback when AI services are unavailable
"""

import logging
from typing import Optional, Dict, Any
import io
import base64

logger = logging.getLogger(__name__)


class SimpleChartAnalysisService:
    """Simple chart analysis service without AI"""
    
    def __init__(self):
        """Initialize simple analysis service"""
        self.available = True
        logger.info("Simple chart analysis service initialized")
    
    def is_available(self) -> bool:
        """Check if service is available"""
        return self.available
    
    def analyze_chart(self, image_bytes: bytes, symbols: list = None) -> Optional[Dict[str, Any]]:
        """
        Provide simple chart analysis without AI
        
        Args:
            image_bytes: Chart image as bytes
            symbols: List of symbols being compared
            
        Returns:
            Dictionary with simple analysis results
        """
        if not self.is_available():
            logger.warning("Simple chart analysis service not available")
            return None
        
        try:
            # Generate simple analysis based on symbols
            analysis = self._generate_simple_analysis(symbols or [])
            
            return {
                'success': True,
                'analysis': analysis,
                'full_analysis': analysis,
                'service_type': 'simple'
            }
            
        except Exception as e:
            logger.error(f"Error in simple chart analysis: {e}")
            return {
                'error': f"Simple analysis failed: {str(e)}",
                'success': False
            }
    
    def _generate_simple_analysis(self, symbols: list) -> str:
        """
        Generate simple analysis based on symbols
        
        Args:
            symbols: List of symbols being compared
            
        Returns:
            Simple analysis text
        """
        if not symbols:
            symbols = ["активы"]
        
        symbol_names = ", ".join(symbols[:3])  # Limit to first 3 symbols
        
        analysis_parts = [
            f"📊 **Простой анализ графика**",
            "",
            f"**Анализируемые активы:** {symbol_names}",
            "",
            "**Основные наблюдения:**",
            "• График показывает накопленную доходность активов",
            "• Время отображается по горизонтальной оси",
            "• Доходность показана по вертикальной оси",
            "",
            "**Рекомендации:**",
            "• Обратите внимание на общий тренд (восходящий/нисходящий)",
            "• Сравните производительность разных активов",
            "• Учитывайте волатильность при принятии решений",
            "",
            "💡 **Примечание:** Для детального AI-анализа используйте доступные AI сервисы"
        ]
        
        return "\n".join(analysis_parts)
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status information
        
        Returns:
            Dictionary with service status
        """
        return {
            'available': self.is_available(),
            'service_type': 'simple',
            'description': 'Simple chart analysis without AI'
        }
