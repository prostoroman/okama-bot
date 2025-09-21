#!/usr/bin/env python3
"""
Тест для проверки парсинга markdown таблицы
"""

def test_markdown_parsing():
    """Тест парсинга markdown таблицы"""
    try:
        import pandas as pd
        
        # Тестовая markdown таблица
        test_table = """| Метрика | Значение |
|---------|----------|
| CAGR (5 лет) | 12.45% |
| Волатильность | 18.32% |
| Коэффициент Шарпа | 0.68 |
| Максимальная просадка | -15.23% |"""
        
        print("Тестируем парсинг markdown таблицы...")
        print("Исходная таблица:")
        print(test_table)
        print("\n" + "="*50 + "\n")
        
        # Имитируем логику парсинга из bot.py
        lines = test_table.strip().split('\n')
        
        # Find the separator line (contains |---|)
        separator_line = None
        separator_index = -1
        for i, line in enumerate(lines):
            if '|---' in line or '| ---' in line:
                separator_line = line
                separator_index = i
                break
        
        if separator_index == -1:
            print("❌ No separator line found in markdown table")
            return False
        
        # Extract headers (line before separator)
        if separator_index > 0:
            header_line = lines[separator_index - 1]
            headers = [col.strip() for col in header_line.split('|')[1:-1]]  # Remove empty first/last elements
        else:
            print("❌ No header line found before separator")
            return False
        
        print(f"Headers: {headers}")
        
        # Extract data rows (lines after separator)
        data_rows = []
        for i in range(separator_index + 1, len(lines)):
            line = lines[i].strip()
            if line and line.startswith('|') and line.endswith('|'):
                # Split by | and remove empty first/last elements
                row_data = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(row_data) == len(headers):
                    data_rows.append(row_data)
        
        print(f"Data rows: {data_rows}")
        
        if not data_rows:
            print("❌ No data rows found in markdown table")
            return False
        
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=headers)
        
        print("✅ Таблица успешно распарсена!")
        print(f"Размер DataFrame: {df.shape}")
        print("\nDataFrame:")
        print(df)
        print("\nКолонки:", df.columns.tolist())
        return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Запуск теста парсинга markdown таблицы...")
    success = test_markdown_parsing()
    if success:
        print("🎉 Тест прошел успешно!")
    else:
        print("💥 Тест не прошел!")
