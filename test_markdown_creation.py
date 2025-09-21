#!/usr/bin/env python3
"""
Тест для проверки создания markdown таблицы
"""

def test_markdown_table_creation():
    """Тест создания markdown таблицы"""
    try:
        import tabulate
        
        # Тестовые данные
        table_data = [
            ["CAGR (5 лет)", "12.45%"],
            ["Волатильность", "18.32%"],
            ["Коэффициент Шарпа", "0.68"],
            ["Максимальная просадка", "-15.23%"]
        ]
        headers = ["Метрика", "Значение"]
        
        print("Тестируем создание markdown таблицы...")
        print("Исходные данные:")
        print("Headers:", headers)
        print("Table data:", table_data)
        print("\n" + "="*50 + "\n")
        
        # Создаем markdown таблицу
        table_markdown = tabulate.tabulate(table_data, headers=headers, tablefmt="pipe")
        
        print("Созданная markdown таблица:")
        print(table_markdown)
        print("\n" + "="*50 + "\n")
        
        # Теперь парсим ее обратно
        lines = table_markdown.strip().split('\n')
        
        # Find the separator line (contains |---| or |:---|)
        separator_line = None
        separator_index = -1
        for i, line in enumerate(lines):
            if '|---' in line or '| ---' in line or '|:---' in line or '| ---:' in line:
                separator_line = line
                separator_index = i
                break
        
        if separator_index == -1:
            print("❌ No separator line found in markdown table")
            return False
        
        # Extract headers (line before separator)
        if separator_index > 0:
            header_line = lines[separator_index - 1]
            parsed_headers = [col.strip() for col in header_line.split('|')[1:-1]]
        else:
            print("❌ No header line found before separator")
            return False
        
        print(f"Parsed headers: {parsed_headers}")
        
        # Extract data rows (lines after separator)
        data_rows = []
        for i in range(separator_index + 1, len(lines)):
            line = lines[i].strip()
            if line and line.startswith('|') and line.endswith('|'):
                row_data = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(row_data) == len(parsed_headers):
                    data_rows.append(row_data)
        
        print(f"Parsed data rows: {data_rows}")
        
        if not data_rows:
            print("❌ No data rows found in markdown table")
            return False
        
        print("✅ Таблица успешно создана и распарсена!")
        return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Запуск теста создания markdown таблицы...")
    success = test_markdown_table_creation()
    if success:
        print("🎉 Тест прошел успешно!")
    else:
        print("💥 Тест не прошел!")
