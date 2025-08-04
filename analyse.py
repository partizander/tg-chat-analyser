import json
import os
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime

EXPORT_FOLDER = "path_to_export_folder"  # замени на путь до папки с экспортом
FILENAME = "result.json"  # или другой, если переименован

# Загрузка JSON
with open(os.path.join(EXPORT_FOLDER, FILENAME), 'r', encoding='utf-8') as f:
    data = json.load(f)

# Извлекаем дату сообщений
messages = data['messages']
dates = [
    datetime.fromisoformat(msg['date']).date()
    for msg in messages
    if msg['type'] == 'message'
]

# Считаем количество сообщений по дням
date_counts = Counter(dates)
sorted_dates = sorted(date_counts.items())

# Рисуем
x = [str(d[0]) for d in sorted_dates]
y = [d[1] for d in sorted_dates]

plt.figure(figsize=(14, 6))
plt.bar(x, y)
plt.xticks(rotation=45, fontsize=8)
plt.title("Количество сообщений по дням")
plt.xlabel("Дата")
plt.ylabel("Сообщений")
plt.tight_layout()
plt.show()
