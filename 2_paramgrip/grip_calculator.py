#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
grip_calculator.py
──────────────────
Промежуточный слой между BiometriScan и ParamGrip.

Принимает: grip_params.json (из analyze.py)
Выдаёт:   grip_dimensions.json (параметры для FreeCAD Spreadsheet)

Биометрические формулы основаны на антропометрических
пропорциях спортивных рукояток (ISSF 10m air rifle/pistol).

Использование:
    python grip_calculator.py hand_scan_params.json
    python grip_calculator.py top_view_params.json
"""

import json
import sys
import math
from pathlib import Path


# ───────────────────────────────────────────
# КОНСТАНТЫ И КОЭФФИЦИЕНТЫ
# ───────────────────────────────────────────

# Пропорциональные коэффициенты
# Источник: антропометрический анализ спортивных рукояток
COEFF = {
    # Длина рукоятки = k × длина ладони
    'Lr_short':  0.75,   # короткий хват (Ch < 0.75 × Cp)
    'Lr_medium': 0.80,   # средний хват
    'Lr_long':   0.85,   # длинный хват (Ch > 1.1 × Cp)

    # Толщина рукоятки
    'Tr_palm':   0.45,   # от толщины ладони
    'Tr_grip':   3.0,    # делитель от Ch

    # Ширина рукоятки
    'Wr':        0.55,   # от ширины ладони

    # Полка под ладонь (palm shelf)
    'Hp':        0.18,   # от длины ладони

    # Глубина под пальцы
    'Df':        20.0,   # делитель от средней длины пальцев

    # Угол наклона рукоятки (градусы)
    'theta_short':  108, # короткий указательный (Lf1/Lp < 0.25)
    'theta_medium': 112, # средний
    'theta_long':   115, # длинный (Lf1/Lp > 0.27)

    # Корректировка угла от хвата
    'theta_adj_short': -2,
    'theta_adj_long':  +3,
}

# Пороги классификации типа руки
HAND_TYPE = {
    'Ch_short_ratio': 0.75,  # Ch < 0.75 × Cp → тип A
    'Ch_long_ratio':  1.10,  # Ch > 1.10 × Cp → тип C
    'Lf1_short':      0.25,  # Lf1/Lp < 0.25 → короткий указательный
    'Lf1_long':       0.27,  # Lf1/Lp > 0.27 → длинный указательный
}


# ───────────────────────────────────────────
# МАППИНГ BiometriScan → calc_grip параметры
# ───────────────────────────────────────────

def map_biometriscan_to_calc(scan_params: dict) -> dict:
    """
    Переводит параметры из BiometriScan JSON в параметры calc_grip.

    BiometriScan              → calc_grip
    ─────────────────────────────────────
    palm_length               → Lp
    palm_width_max            → Wp
    palm_depth_max            → Tp
    grip_diameter             → Ch  (цилиндр = физический grip arc)
    width_at_fingers          → Ch_proxy если grip_diameter нет
    trigger_reach_est         → Lf1 (оценочно)
    grip_height               → Lf2, Lf3, Lf4 (оценочно)
    """
    p = scan_params.get('grip_params', scan_params)

    Lp = p.get('palm_length', 180.0)
    Wp = p.get('palm_width_max', 85.0)
    Tp = p.get('palm_depth_max') or p.get('grip_thickness_rec', 28.0) / 0.85

    # Ch — из диаметра калиброванного цилиндра (основной метод)
    # Если нет — оцениваем из ширины ладони
    Ch = p.get('grip_diameter')
    if Ch is None:
        Ch = Wp * 0.45
        print(f"  [!] grip_diameter не найден — оценка Ch = {Ch:.1f}мм (±5мм)")

    # Cp — обхват ладони
    # Если нет прямого измерения — оцениваем из ширины и глубины
    Cp = p.get('palm_circumference')
    if Cp is None:
        # Эллипс: периметр ≈ π × (3(a+b) - √((3a+b)(a+3b)))
        a = Wp / 2.0
        b = Tp / 2.0
        Cp = math.pi * (3*(a+b) - math.sqrt((3*a+b)*(a+3*b)))
        print(f"  [!] palm_circumference не найден — расчёт Cp = {Cp:.1f}мм")

    # Длины пальцев
    # Если есть отдельные — используем, иначе оцениваем из grip_height
    grip_h = p.get('grip_height', Lp * 0.60)
    trigger = p.get('trigger_reach_est', Lp * 0.26)

    Lf1 = p.get('finger_length_index',   trigger)          # указательный
    Lf2 = p.get('finger_length_middle',  grip_h * 0.42)   # средний
    Lf3 = p.get('finger_length_ring',    grip_h * 0.40)   # безымянный
    Lf4 = p.get('finger_length_pinky',   grip_h * 0.32)   # мизинец

    return {
        'Lp': float(Lp),
        'Wp': float(Wp),
        'Tp': float(Tp),
        'Ch': float(Ch),
        'Cp': float(Cp),
        'Lf1': float(Lf1),
        'Lf2': float(Lf2),
        'Lf3': float(Lf3),
        'Lf4': float(Lf4),
    }


# ───────────────────────────────────────────
# КЛАССИФИКАЦИЯ ТИПА РУКИ
# ───────────────────────────────────────────

def classify_hand(Lp, Wp, Tp, Ch, Cp, Lf1, **kwargs) -> dict:
    """
    Определяет тип руки (A/B/C) и размер (XXS..XL).
    """
    # Тип по соотношению хвата
    ch_ratio = Ch / Cp if Cp > 0 else 1.0
    if ch_ratio < HAND_TYPE['Ch_short_ratio']:
        hand_type = 'A'
        hand_desc = 'короткая широкая ладонь, короткие пальцы'
    elif ch_ratio > HAND_TYPE['Ch_long_ratio']:
        hand_type = 'C'
        hand_desc = 'узкая ладонь, длинные пальцы'
    else:
        hand_type = 'B'
        hand_desc = 'средняя ладонь'

    # Размер по ширине ладони
    size_map = [
        ('XXS', 67, 73),
        ('XS',  72, 78),
        ('S',   78, 84),
        ('M',   85, 91),
        ('L',   92, 98),
        ('XL',  98, 104),
    ]
    size = 'M'
    for s, lo, hi in size_map:
        if lo <= Wp <= hi:
            size = s
            break
    if Wp < 67:
        size = 'XXS'
    elif Wp > 104:
        size = 'XL'

    return {
        'hand_type':  hand_type,
        'hand_desc':  hand_desc,
        'size':       size,
        'ch_ratio':   round(ch_ratio, 3),
    }


# ───────────────────────────────────────────
# ОСНОВНОЙ РАСЧЁТ
# ───────────────────────────────────────────

def calc_grip(Lp, Wp, Tp, Ch, Cp, Lf1, Lf2, Lf3, Lf4) -> dict:
    """
    Вычисляет параметры рукоятки из биометрии ладони.
    Все размеры в мм.
    """
    avg_Lf = (Lf2 + Lf3 + Lf4) / 3.0
    ch_ratio = Ch / Cp if Cp > 0 else 1.0

    # Длина рукоятки
    if ch_ratio < HAND_TYPE['Ch_short_ratio']:
        Lr = COEFF['Lr_short'] * Lp
    elif ch_ratio > HAND_TYPE['Ch_long_ratio']:
        Lr = COEFF['Lr_long'] * Lp
    else:
        Lr = COEFF['Lr_medium'] * Lp

    # Толщина рукоятки
    Tr = min(COEFF['Tr_palm'] * Tp, Ch / COEFF['Tr_grip'])

    # Ширина рукоятки
    Wr = COEFF['Wr'] * Wp

    # Полка под ладонь (palm shelf / M1)
    Hp = COEFF['Hp'] * Lp

    # Глубина канавок под пальцы
    Df = avg_Lf / COEFF['Df']

    # Угол наклона рукоятки
    lf1_ratio = Lf1 / Lp if Lp > 0 else 0.26
    if lf1_ratio > HAND_TYPE['Lf1_long']:
        theta = COEFF['theta_long']
    elif lf1_ratio >= HAND_TYPE['Lf1_short']:
        theta = COEFF['theta_medium']
    else:
        theta = COEFF['theta_short']

    # Корректировка угла от типа хвата
    if ch_ratio < HAND_TYPE['Ch_short_ratio']:
        theta += COEFF['theta_adj_short']
    elif ch_ratio > HAND_TYPE['Ch_long_ratio']:
        theta += COEFF['theta_adj_long']

    # Дополнительные параметры для FreeCAD
    thumb_radius    = Wp * 0.40   # радиус упора большого пальца
    flare_height    = Tp * 0.80   # высота расширения у запястья
    palm_swell_pos  = 50.0        # позиция максимума palm swell (% от низа)

    # Если указательный длиннее среднего — сместить palm swell вверх
    if Lf1 > Lf2:
        palm_swell_pos = 55.0

    return {
        # Основные параметры рукоятки
        'Lr':             round(Lr, 1),
        'Tr':             round(Tr, 1),
        'Wr':             round(Wr, 1),
        'Hp':             round(Hp, 1),
        'Df':             round(Df, 1),
        'theta':          round(theta, 1),

        # Для модулей
        'thumb_radius':   round(thumb_radius, 1),
        'flare_height':   round(flare_height, 1),
        'palm_swell_pos': round(palm_swell_pos, 1),

        # Промежуточные
        'avg_Lf':         round(avg_Lf, 1),
        'ch_ratio':       round(ch_ratio, 3),
        'lf1_ratio':      round(lf1_ratio, 3),
    }


# ───────────────────────────────────────────
# МАППИНГ → FreeCAD Spreadsheet
# ───────────────────────────────────────────

def to_freecad_params(raw: dict, dims: dict, classification: dict) -> dict:
    """
    Финальный маппинг всех параметров для FreeCAD Spreadsheet.
    Имена совпадают с переменными в grip_skeleton_template.FCStd.
    """
    return {
        # === БИОМЕТРИЯ (из BiometriScan) ===
        'palm_length':          raw['Lp'],
        'palm_width_max':       raw['Wp'],
        'palm_depth_max':       raw['Tp'],
        'grip_diameter':        raw['Ch'],
        'palm_circumference':   raw['Cp'],

        # === ГЕОМЕТРИЯ РУКОЯТКИ (из calc_grip) ===
        'grip_height':          dims['Lr'],
        'grip_thickness':       dims['Tr'],
        'grip_width':           dims['Wr'],
        'palm_shelf_height':    dims['Hp'],
        'finger_groove_depth':  dims['Df'],
        'grip_angle_deg':       dims['theta'],

        # === МОДУЛИ (начальные позиции) ===
        'M1_palm_shelf_init':   dims['Hp'],
        'M2_thumb_radius':      dims['thumb_radius'],
        'M3_backstrap_init':    dims['Tr'],
        'M4_pinky_shelf_init':  dims['avg_Lf'] * 0.15,
        'M6_palm_swell_pos':    dims['palm_swell_pos'],

        # === КЛАССИФИКАЦИЯ ===
        'hand_type':            classification['hand_type'],
        'grip_size':            classification['size'],

        # === МОНТАЖ FWB 800X (фиксированные — вымерять!) ===
        'fwb_screw_1_y':        0,    # TODO
        'fwb_screw_2_y':        0,    # TODO
        'fwb_screw_dia':        4.0,  # M4, проверить
        'fwb_rail_width':       0,    # TODO
        'fwb_rail_depth':       0,    # TODO
    }


# ───────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────

def process(input_path: str) -> dict:
    print(f"\n{'='*50}")
    print(f"GRIP CALCULATOR")
    print(f"{'='*50}")
    print(f"Входной файл: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)

    # Источник данных
    source = scan_data.get('source_type', 'unknown')
    accuracy = scan_data.get('accuracy_note', '')
    print(f"Источник: {source}")
    if accuracy:
        print(f"Точность: {accuracy}")

    # Шаг 1: маппинг BiometriScan → calc параметры
    print("\n[1/3] Маппинг параметров...")
    raw = map_biometriscan_to_calc(scan_data)
    for k, v in raw.items():
        print(f"  {k:<6} = {v:.1f} мм")

    # Шаг 2: классификация
    print("\n[2/3] Классификация руки...")
    classification = classify_hand(**raw)
    print(f"  Тип:    {classification['hand_type']} — {classification['hand_desc']}")
    print(f"  Размер: {classification['size']}")
    print(f"  Ch/Cp:  {classification['ch_ratio']:.3f}")

    # Шаг 3: расчёт параметров рукоятки
    print("\n[3/3] Расчёт геометрии рукоятки...")
    dims = calc_grip(**raw)

    print(f"\n{'─'*50}")
    print(f"ПАРАМЕТРЫ РУКОЯТКИ")
    print(f"{'─'*50}")
    labels = {
        'Lr':             'Высота рукоятки',
        'Tr':             'Толщина',
        'Wr':             'Ширина',
        'Hp':             'Полка под ладонь (M1 init)',
        'Df':             'Глубина под пальцы',
        'theta':          'Угол наклона',
        'thumb_radius':   'Радиус упора большого пальца',
        'flare_height':   'Высота расширения у запястья',
        'palm_swell_pos': 'Позиция palm swell',
    }
    for k, label in labels.items():
        unit = '°' if k == 'theta' else 'мм' if k != 'palm_swell_pos' else '%'
        print(f"  {label:<35} {dims[k]}{unit}")

    # Финальный маппинг для FreeCAD
    freecad_params = to_freecad_params(raw, dims, classification)

    result = {
        'source_file':      input_path,
        'source_type':      source,
        'classification':   classification,
        'raw_biometrics':   raw,
        'grip_dimensions':  dims,
        'freecad_params':   freecad_params,
    }

    # Сохранение
    out_path = input_path.replace('_params.json', '_grip_dims.json')
    if out_path == input_path:
        out_path = input_path.replace('.json', '_grip_dims.json')

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Сохранено: {out_path}")
    print(f"  Следующий шаг: python freecad_load_params.py {out_path}")

    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python grip_calculator.py hand_params.json")
        sys.exit(1)

    process(sys.argv[1])
