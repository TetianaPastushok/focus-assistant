#!/usr/bin/env python
"""Test script to verify CSV logging works"""
from csv_logger import SessionCsvLogger
import time

# Тест логування
logger = SessionCsvLogger('test_session.csv')
logger.start()

# Симулюємо метрики
test_metrics = {
    'blinks_total': 10,
    'bpm': 15,
    'perclos': 8.5,
    'focus_duration_sec': 120,
    'distractions': 2,
    'focus_score': 0.82,
    'zone': 'NORMAL',
    'mode': 'assistant',
    'attention_state': 'NORMAL',
    'continuous_inattention_sec': 0.0,
    'accumulated_inattention_sec': 0.0,
    'intervention_level': '',
    'intervention_reason': '',
    'intervention_message': '',
    'event_type': '',
}

# Пишемо
current_time = time.time()
logger.log_once_per_second(current_time, test_metrics)
time.sleep(1.1)
logger.log_once_per_second(current_time + 1.5, test_metrics)

logger.stop()
print('✅ CSV тест успішний!')
print('   Файл: test_session.csv')
