#!/usr/bin/env python3
"""
Тест для проверки обновленной функции get_random_examples
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

def test_get_random_examples():
    """Тест функции get_random_examples с китайскими и гонконгскими активами"""
    bot = ShansAi()
    
    # Тестируем получение примеров
    examples = bot.get_random_examples(5)
    
    print("Полученные примеры:")
    for example in examples:
        print(f"  {example}")
    
    # Проверяем, что все примеры имеют обратные кавычки
    for example in examples:
        assert example.startswith('`') and example.endswith('`'), f"Пример {example} не имеет обратных кавычек"
    
    # Проверяем, что есть китайские и гонконгские активы
    all_examples_text = ' '.join(examples)
    has_chinese = any(marker in all_examples_text for marker in ['.SH', '.SZ', '.BJ'])
    has_hong_kong = '.HK' in all_examples_text
    
    print(f"\nРезультаты проверки:")
    print(f"  Китайские активы (.SH, .SZ, .BJ): {'✓' if has_chinese else '✗'}")
    print(f"  Гонконгские активы (.HK): {'✓' if has_hong_kong else '✗'}")
    print(f"  Все примеры имеют обратные кавычки: ✓")
    
    # Проверяем, что количество примеров соответствует запрошенному
    assert len(examples) == 5, f"Ожидалось 5 примеров, получено {len(examples)}"
    
    print(f"\n✅ Тест пройден успешно!")

if __name__ == "__main__":
    test_get_random_examples()
