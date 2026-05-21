# Biometric Grip Pipeline
## FWB 800X / Sport Shooting — Full Development Stack

---

## Overview

Трёхуровневый pipeline для генерации анатомической рукоятки под конкретную ладонь стрелка.

```
ИСТОЧНИК ДАННЫХ (на выбор)
  ├── Скан руки (PLY/OBJ)            →  analyze_scan.py
  └── Фото + ChArUco пластина (JPG)  →  analyze_photo.py
        ├── Фото 1: ладонь вверх на пластине
        └── Фото 2: хват цилиндра сбоку + пластина
              ↓
         analyze.py  (единая точка входа)
              ↓
         grip_params.json
              ↓
         grip_calculator.py  ← NEW: биометрия → геометрия рукоятки
         (пропорциональные формулы, классификация типа руки A/B/C,
          размер XXS..XL, маппинг в FreeCAD параметры)
              ↓
         grip_dimensions.json + freecad_params
              ↓
[FreeCAD] Параметрический скелет + монтажные точки FWB
              ↓ STEP
[Fusion 360] Loft, органика, T-Splines, финальный solid
              ↓ STL/OBJ
[Blender] Voronoi / lattice на grip zone
              ↓ STL
[Slicer] Печать (PA12 / PETG / CF)
```

---

## Инструменты калибровки (печатаются отдельно)

```
charuco_plate    — ChArUco пластина A4 или 300×300мм
cylinder_set     — набор цилиндров ∅28/32/36/40/44/48мм
```

---

## Точность по источнику данных

| Источник | Точность | Покрытие параметров | Усилие |
|---|---|---|---|
| Скан Revopoint MINI 2 | ±0.2мм | 100% | Высокое |
| Скан iPhone LiDAR | ±0.5мм | 100% | Среднее |
| Фото 1 + Фото 2 + цилиндр | ±1-2мм | ~95% | Низкое |
| Ручной обмер | ±0.5мм | ~80% | Низкое |

Для первого прототипа — фото + цилиндр достаточно. Скан нужен на финальной подгонке.

---

## Стек технологий

| Инструмент | Роль | Лицензия |
|---|---|---|
| Python 3.10+ | Анализ скана/фото, параметры | Бесплатно |
| Open3D | Работа с point cloud / PLY | Бесплатно |
| OpenCV | Обработка фото, калибровка | Бесплатно |
| MediaPipe | Hand landmarks с фото | Бесплатно |
| FreeCAD 0.21+ | Параметрический скелет | Бесплатно |
| Fusion 360 | Органические поверхности, loft | Personal free / Commercial |
| Blender 4.x | Voronoi, Geometry Nodes | Бесплатно |

---

## Зависимости Python

```bash
pip install open3d numpy scipy mediapipe opencv-python
```

---

## Шаг 1А — Сканирование руки (высокая точность)

### Требования к скану
- Формат: **PLY** или **OBJ** (point cloud или mesh)
- Ладонь смотрит **вверх**, пальцы вместе, большой палец в натуральном положении
- Скан делать в **естественном положении хвата** — как будто держишь рукоятку
- Рекомендуемое оборудование:
  - Revopoint MINI 2 — лучшая точность для кисти
  - iPhone 12+ LiDAR + Scaniverse — приемлемо
  - Фотограмметрия (Meshroom) — бесплатно, дольше

### Ориентация при сканировании
```
Запястье → -Y
Пальцы   → +Y
Тыльная  → -Z
Ладонь   → +Z
Правая   → +X
Левая    → -X
```

---

## Шаг 1Б — Фото с калиброванной рамкой (быстрый метод)

Когда скан недоступен. Точность ±1-2мм, достаточно для первых 1-2 прототипов.

### Подготовка рамки

Распечатать на A4 (не масштабировать — 100%):
- Шахматная сетка 10×10мм, 8×8 клеток
- Или ArUco маркеры по углам (генерировать на aruco-markers.com)

Проверка: линейкой замерить распечатанную клетку — должно быть ровно 10мм.

### Калибровочная пластина

Вместо бумажной рамки — **напечатанная ChArUco пластина** (PETG, первый слой двухцвет):
- Паттерн: ChArUco DICT_4X4_250
- Размер: A4 (210×285мм) или 300×300мм
- Клетка: 15мм (A4) / 20мм (300×300)
- **Базовая линия** — горизонтальная черта на известной Y-позиции
- **Физический бортик 2мм** вдоль базовой линии — запястье упирается физически

```
┌──────────────────────────────┐
│   [ChArUco паттерн]          │
│                              │
│   ← пальцы / ладонь          │
│                              │
│▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬│ ← wrist baseline (бортик)
│   ← запястье ниже            │
└──────────────────────────────┘
```

Алгоритм знает Y базовой линии в мм — не угадывает где запястье.

### Набор калибровочных цилиндров

Печатаются отдельно, используются для фото 2:

```
∅28мм / ∅32мм / ∅36мм / ∅40мм / ∅44мм / ∅48мм
Длина: 100мм, стенка: 3мм, материал: PETG
```

Протокол подбора: стрелок берёт каждый в хват → выбирает комфортный → это и есть `grip_diameter`.

### Протокол съёмки

**Фото 1 — ладонь вверх, вид сверху** (обязательное):
```
- Рука лежит ЛАДОНЬЮ ВВЕРХ на ChArUco пластине
- Складка запястья упирается в бортик базовой линии
- Пальцы слегка разведены, естественно
- Большой палец отведён под ~45°
- Камера строго вертикально над рукой
- Вся пластина в кадре
- Равномерное освещение, без теней
```

Что детектируется:
```
  palm_width_max      ✓  (MediaPipe landmarks)
  palm_length         ✓  (от baseline до кончиков)
  width_at_fingers    ✓
  width_at_wrist      ✓
  trigger_reach_est   ✓
  thumb_angle         ✓
  palm_depth_max      ✗  (нет — берём из фото 2)
```

**Фото 2 — хват цилиндра, вид сбоку** (для глубины и хвата):
```
- Стрелок держит подобранный цилиндр в натуральном хвате
- ChArUco пластина стоит вертикально рядом
- Съёмка строго сбоку (по оси большого пальца)
- Цилиндр полностью в кадре
- Пластина полностью в кадре
```

Что детектируется:
```
  grip_diameter       ✓  (известен из маркировки цилиндра)
  grip_thickness_rec  ✓  (= grip_diameter)
  grip_height         ✓  (cv2.HoughCircles + контур руки)
  trigger_reach_est   ✓  (положение указательного)
  thumb_position      ✓  (выступ большого пальца)
  backstrap_curve     ✓  (контур тыльной стороны)
```

**Фото 3 — ладонь лодочкой, вид спереди** (опциональное, для M6):
```
- Рука сложена лодочкой (пальцы вместе, максимальная вогнутость)
- ChArUco пластина вертикально рядом
- Съёмка спереди, по оси среднего пальца
- Вся пластина в кадре
```

Что детектируется:
```
  depth_cup           ✓  максимальная глубина вогнутости
  delta = depth_cup - depth_grip → диапазон регулировки M6
```

Если delta большая → ладонь гибкая, M6 работает в широком диапазоне.
Если маленькая → ладонь жёсткая, M6 минимальный.

### Итоговая таблица параметров по источникам

| Параметр | Фото 1 | Фото 2 + цилиндр | Скан |
|---|---|---|---|
| palm_width_max | ✓ | — | ✓ |
| palm_length | ✓ | — | ✓ |
| width_at_fingers | ✓ | — | ✓ |
| thumb_angle | ✓ | — | ✓ |
| grip_diameter | — | ✓✓ физически | ✓ |
| grip_height | — | ✓ | ✓ |
| trigger_reach | ✓ | ✓ | ✓ |
| thumb_position | — | ✓ | ✓ |
| backstrap_curve | — | ✓ | ✓ |
| palm_depth_max | — | ✓✓ | ✓ |

---

## Шаг 2А — Python: анализ скана

### `analyze_scan.py`

```python
import open3d as o3d
import numpy as np
import json
import sys
from scipy.spatial import ConvexHull

def load_scan(filepath):
    """Загрузка PLY или OBJ."""
    if filepath.endswith('.ply'):
        pcd = o3d.io.read_point_cloud(filepath)
    elif filepath.endswith('.obj'):
        mesh = o3d.io.read_triangle_mesh(filepath)
        pcd = mesh.sample_points_uniformly(number_of_points=50000)
    else:
        raise ValueError("Поддерживается PLY или OBJ")
    
    # Удаление выбросов
    pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
    return pcd

def orient_hand(pcd):
    """
    PCA-ориентация: главная ось руки → Y.
    Предполагает скан ладонью вверх.
    """
    points = np.asarray(pcd.points)
    centroid = points.mean(axis=0)
    centered = points - centroid
    
    cov = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    
    # Сортировка: наибольшее собственное значение → главная ось
    idx = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, idx]
    
    # Трансформируем точки
    rotated = centered @ eigenvectors
    pcd_oriented = o3d.geometry.PointCloud()
    pcd_oriented.points = o3d.utility.Vector3dVector(rotated)
    
    return pcd_oriented, centroid, eigenvectors

def extract_zones(points):
    """
    Разбивка руки на зоны по Y:
    - fingers: верхние 40%
    - palm:    средние 35%
    - wrist:   нижние 25%
    """
    y_min, y_max = points[:, 1].min(), points[:, 1].max()
    y_range = y_max - y_min
    
    zones = {
        'fingers': points[points[:, 1] > y_min + y_range * 0.60],
        'palm':    points[(points[:, 1] > y_min + y_range * 0.25) &
                          (points[:, 1] < y_min + y_range * 0.60)],
        'wrist':   points[points[:, 1] < y_min + y_range * 0.25],
        'thumb':   points[points[:, 0] > points[:, 0].mean() + 
                          points[:, 0].std() * 0.5],  # правая сторона
    }
    return zones

def measure_width_profile(points, n_slices=10):
    """
    Профиль ширины вдоль Y — n сечений.
    Возвращает список {y_pct, width_mm}.
    """
    y_min, y_max = points[:, 1].min(), points[:, 1].max()
    y_range = y_max - y_min
    profile = []
    
    for i in range(n_slices):
        y_lo = y_min + y_range * (i / n_slices)
        y_hi = y_min + y_range * ((i + 1) / n_slices)
        slice_pts = points[(points[:, 1] >= y_lo) & (points[:, 1] < y_hi)]
        
        if len(slice_pts) > 10:
            width = slice_pts[:, 0].ptp()
            depth = slice_pts[:, 2].ptp()
            profile.append({
                'y_pct': round((i + 0.5) / n_slices * 100, 1),
                'width_mm': round(float(width), 1),
                'depth_mm': round(float(depth), 1),
            })
    
    return profile

def compute_grip_params(points, zones):
    """
    Основные параметры для FreeCAD Spreadsheet.
    Все размеры в мм.
    """
    palm = zones['palm']
    fingers = zones['fingers']
    wrist = zones['wrist']
    
    params = {
        # === ГАБАРИТЫ ===
        'palm_width_max':     round(float(palm[:, 0].ptp()), 1),
        'palm_length':        round(float(points[:, 1].ptp()), 1),
        'palm_depth_max':     round(float(palm[:, 2].ptp()), 1),
        
        # === ЗОНЫ ===
        'width_at_fingers':   round(float(fingers[:, 0].ptp()), 1),
        'width_at_palm':      round(float(palm[:, 0].ptp()), 1),
        'width_at_wrist':     round(float(wrist[:, 0].ptp()), 1),
        'depth_at_fingers':   round(float(fingers[:, 2].ptp()), 1),
        'depth_at_palm':      round(float(palm[:, 2].ptp()), 1),
        
        # === РАСЧЁТНЫЕ ДЛЯ РУКОЯТКИ ===
        # Рекомендуемая толщина grip — 85% от глубины ладони
        'grip_thickness_rec': round(float(palm[:, 2].ptp()) * 0.85, 1),
        
        # Palm swell — позиция максимального выпуклости в % от низа
        'palm_swell_y_pct':   round(
            float((palm[:, 1].mean() - points[:, 1].min()) /
                  points[:, 1].ptp() * 100), 1
        ),
        
        # Ширина запястья — для flare рукоятки
        'wrist_width':        round(float(wrist[:, 0].ptp()), 1),
        
        # Высота от запястья до начала пальцев
        'grip_height':        round(float(
            fingers[:, 1].min() - wrist[:, 1].max()), 1),
        
        # === СПЕЦИФИКА ISSF ПИСТОЛЕТ ===
        # Расстояние до спуска — 70% ширины указательного пальца
        # (грубая оценка, уточнять на примерке)
        'trigger_reach_est':  round(float(fingers[:, 0].ptp()) * 0.70, 1),
    }
    
    return params

def analyze_hand_scan(filepath):
    print(f"[1/5] Загрузка: {filepath}")
    pcd = load_scan(filepath)
    print(f"      Точек: {len(pcd.points)}")
    
    print("[2/5] Ориентация по PCA...")
    pcd_oriented, centroid, rotation = orient_hand(pcd)
    points = np.asarray(pcd_oriented.points)
    
    print("[3/5] Разбивка на зоны...")
    zones = extract_zones(points)
    for name, zone in zones.items():
        print(f"      {name}: {len(zone)} точек")
    
    print("[4/5] Профиль ширины...")
    profile = measure_width_profile(points)
    
    print("[5/5] Вычисление параметров...")
    params = compute_grip_params(points, zones)
    
    result = {
        'source_file': filepath,
        'point_count': len(pcd.points),
        'grip_params': params,
        'width_profile': profile,
    }
    
    return result

# === MAIN ===
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python analyze_scan.py hand_scan.ply")
        sys.exit(1)
    
    filepath = sys.argv[1]
    result = analyze_hand_scan(filepath)
    
    # Вывод параметров
    print("\n" + "="*50)
    print("ПАРАМЕТРЫ РУКОЯТКИ")
    print("="*50)
    for key, val in result['grip_params'].items():
        print(f"  {key:<30} {val} мм")
    
    # Сохранение JSON
    out_file = filepath.replace('.ply', '_params.json').replace('.obj', '_params.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nСохранено: {out_file}")
```

---

## Шаг 2Б — Python: анализ фото

### `analyze_photo.py`

```python
import cv2
import numpy as np
import mediapipe as mp
import json
import sys
from pathlib import Path

# MediaPipe hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# ───────────────────────────────────────────
# КАЛИБРОВКА
# ───────────────────────────────────────────

def detect_calibration_grid(image, grid_mm=10.0, grid_cols=8, grid_rows=8):
    """
    Находит шахматную калибровочную сетку на фото.
    Возвращает px_per_mm или None если не найдена.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    pattern_size = (grid_cols - 1, grid_rows - 1)  # внутренние углы
    
    ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
    
    if not ret:
        print("  [!] Шахматка не найдена — пробуем ArUco")
        return detect_aruco_calibration(image)
    
    # Уточняем углы
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
    
    # Расстояние между соседними углами в пикселях
    dists = []
    for i in range(len(corners) - 1):
        pt1 = corners[i][0]
        pt2 = corners[i + 1][0]
        d = np.linalg.norm(pt2 - pt1)
        dists.append(d)
    
    px_per_mm = np.median(dists) / grid_mm
    print(f"  Калибровка (шахматка): {px_per_mm:.3f} px/мм")
    return px_per_mm

def detect_aruco_calibration(image):
    """
    Fallback: калибровка по ArUco маркерам.
    Маркер 4x4_50, размер 40мм.
    """
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, params)
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)
    
    if ids is None or len(ids) < 2:
        print("  [!] ArUco не найден — калибровка невозможна")
        return None
    
    # Размер маркера 40мм — берём сторону первого маркера
    c = corners[0][0]
    side_px = np.linalg.norm(c[1] - c[0])
    px_per_mm = side_px / 40.0
    print(f"  Калибровка (ArUco): {px_per_mm:.3f} px/мм")
    return px_per_mm

# ───────────────────────────────────────────
# LANDMARKS РУКИ
# ───────────────────────────────────────────

LANDMARK = mp_hands.HandLandmark

def detect_hand_landmarks(image):
    """
    Возвращает landmarks в пикселях.
    MediaPipe даёт 21 точку.
    """
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image.shape[:2]
    
    with mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.5
    ) as hands:
        result = hands.process(rgb)
    
    if not result.multi_hand_landmarks:
        raise RuntimeError("Рука не обнаружена на фото")
    
    lm = result.multi_hand_landmarks[0].landmark
    
    # Конвертируем в пиксели
    pts = {}
    for name, idx in {
        'WRIST':         LANDMARK.WRIST,
        'THUMB_CMC':     LANDMARK.THUMB_CMC,
        'THUMB_MCP':     LANDMARK.THUMB_MCP,
        'THUMB_TIP':     LANDMARK.THUMB_TIP,
        'INDEX_MCP':     LANDMARK.INDEX_FINGER_MCP,
        'INDEX_TIP':     LANDMARK.INDEX_FINGER_TIP,
        'MIDDLE_MCP':    LANDMARK.MIDDLE_FINGER_MCP,
        'MIDDLE_TIP':    LANDMARK.MIDDLE_FINGER_TIP,
        'RING_MCP':      LANDMARK.RING_FINGER_MCP,
        'PINKY_MCP':     LANDMARK.PINKY_MCP,
        'PINKY_TIP':     LANDMARK.PINKY_TIP,
    }.items():
        pts[name] = np.array([lm[idx].x * w, lm[idx].y * h])
    
    return pts

def dist(p1, p2):
    return float(np.linalg.norm(p2 - p1))

# ───────────────────────────────────────────
# ПАРАМЕТРЫ ИЗ ФОТО СВЕРХУ
# ───────────────────────────────────────────

def extract_top_view_params(image_path):
    """
    Фото сверху → 2D параметры.
    """
    print(f"  Загрузка: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Файл не найден: {image_path}")
    
    print("  Калибровка рамки...")
    px_per_mm = detect_calibration_grid(img)
    if px_per_mm is None:
        raise RuntimeError("Не удалось откалибровать рамку")
    
    print("  Детектирование руки...")
    pts = detect_hand_landmarks(img)
    
    def mm(px_dist):
        return round(px_dist / px_per_mm, 1)
    
    # Ширина ладони: от PINKY_MCP до THUMB_CMC (поперёк)
    palm_width = mm(dist(pts['PINKY_MCP'], pts['THUMB_CMC']))
    
    # Длина ладони: от WRIST до MIDDLE_MCP
    palm_length = mm(dist(pts['WRIST'], pts['MIDDLE_MCP']))
    
    # Ширина по пальцам: INDEX_MCP → PINKY_MCP
    width_fingers = mm(dist(pts['INDEX_MCP'], pts['PINKY_MCP']))
    
    # Угол большого пальца (от оси ладони)
    palm_axis = pts['MIDDLE_MCP'] - pts['WRIST']
    thumb_axis = pts['THUMB_TIP'] - pts['THUMB_CMC']
    cos_angle = np.dot(palm_axis, thumb_axis) / (
        np.linalg.norm(palm_axis) * np.linalg.norm(thumb_axis) + 1e-9
    )
    thumb_angle = round(float(np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))), 1)
    
    # Reach до спуска — от WRIST до INDEX_TIP по оси X
    trigger_reach = mm(abs(pts['INDEX_TIP'][0] - pts['WRIST'][0]))
    
    params = {
        'palm_width_max':    palm_width,
        'palm_length':       palm_length,
        'width_at_fingers':  width_fingers,
        'width_at_wrist':    mm(dist(pts['WRIST'], pts['PINKY_MCP'])) * 0.85,
        'trigger_reach_est': trigger_reach,
        'thumb_angle_deg':   thumb_angle,
        # Глубина недоступна из этого фото
        'palm_depth_max':    None,
        'grip_thickness_rec': None,
    }
    
    return params, img, pts, px_per_mm

# ───────────────────────────────────────────
# ПАРАМЕТРЫ ИЗ ФОТО СБОКУ
# ───────────────────────────────────────────

def extract_side_view_params(image_path, px_per_mm_override=None):
    """
    Фото сбоку → глубина охвата.
    """
    print(f"  Загрузка (вид сбоку): {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Файл не найден: {image_path}")
    
    if px_per_mm_override:
        px_per_mm = px_per_mm_override
    else:
        px_per_mm = detect_calibration_grid(img)
        if px_per_mm is None:
            raise RuntimeError("Не удалось откалибровать рамку (сбоку)")
    
    pts = detect_hand_landmarks(img)
    
    def mm(px_dist):
        return round(px_dist / px_per_mm, 1)
    
    # Глубина охвата: по оси перпендикулярной виду сбоку
    # На фото сбоку — это горизонтальный размер сжатой руки
    all_x = [p[0] for p in pts.values()]
    depth_px = max(all_x) - min(all_x)
    palm_depth = mm(depth_px)
    
    # Высота хвата: WRIST → MIDDLE_MCP по вертикали
    grip_height = mm(abs(pts['MIDDLE_MCP'][1] - pts['WRIST'][1]))
    
    params = {
        'palm_depth_max':     palm_depth,
        'grip_thickness_rec': round(palm_depth * 0.85, 1),
        'grip_height':        grip_height,
    }
    
    return params

# ───────────────────────────────────────────
# ВИЗУАЛИЗАЦИЯ
# ───────────────────────────────────────────

def save_debug_image(image, pts, px_per_mm, output_path):
    """Сохраняет фото с нанесёнными точками для проверки."""
    debug = image.copy()
    
    for name, pt in pts.items():
        x, y = int(pt[0]), int(pt[1])
        cv2.circle(debug, (x, y), 5, (0, 255, 0), -1)
        cv2.putText(debug, name, (x + 6, y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 200, 255), 1)
    
    # Масштабная линейка 50мм
    ruler_px = int(50 * px_per_mm)
    cv2.line(debug, (20, 30), (20 + ruler_px, 30), (255, 255, 0), 2)
    cv2.putText(debug, "50mm", (20, 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    cv2.imwrite(output_path, debug)
    print(f"  Debug: {output_path}")

# ───────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────

def analyze_hand_photo(top_view_path, side_view_path=None):
    """
    Основная функция. Принимает 1 или 2 фото.
    Возвращает dict совместимый с analyze_scan.py.
    """
    print("[1/3] Анализ вида сверху...")
    top_params, img, pts, px_per_mm = extract_top_view_params(top_view_path)
    
    # Debug изображение
    debug_path = top_view_path.replace('.jpg', '_debug.jpg').replace('.png', '_debug.png')
    save_debug_image(img, pts, px_per_mm, debug_path)
    
    grip_params = top_params.copy()
    
    if side_view_path:
        print("[2/3] Анализ вида сбоку...")
        side_params = extract_side_view_params(side_view_path, px_per_mm)
        grip_params.update(side_params)
    else:
        print("[2/3] Вид сбоку не предоставлен — глубина будет оценочной")
        # Грубая оценка глубины из ширины (эмпирический коэффициент)
        if grip_params['palm_width_max']:
            estimated_depth = round(grip_params['palm_width_max'] * 0.30, 1)
            grip_params['palm_depth_max'] = estimated_depth
            grip_params['grip_thickness_rec'] = round(estimated_depth * 0.85, 1)
            print(f"  Оценочная глубина: {estimated_depth}мм (±3мм, уточнить)")
    
    # Производные параметры
    if grip_params.get('palm_swell_y_pct') is None:
        grip_params['palm_swell_y_pct'] = 50.0  # по умолчанию центр
    if grip_params.get('width_at_wrist') is None:
        grip_params['width_at_wrist'] = round(grip_params['palm_width_max'] * 0.82, 1)
    
    print("[3/3] Готово.")
    
    result = {
        'source_file': top_view_path,
        'source_type': 'photo_2view' if side_view_path else 'photo_1view',
        'accuracy_note': '±1-2мм (фото). Для финала рекомендуется скан.',
        'grip_params': grip_params,
        'width_profile': [],  # недоступно из фото
    }
    
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python analyze_photo.py top_view.jpg")
        print("  python analyze_photo.py top_view.jpg side_view.jpg")
        sys.exit(1)
    
    top = sys.argv[1]
    side = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = analyze_hand_photo(top, side)
    
    print("\n" + "="*50)
    print("ПАРАМЕТРЫ РУКОЯТКИ")
    print("="*50)
    for key, val in result['grip_params'].items():
        unit = "°" if 'angle' in key else "мм"
        note = " ⚠ оценка" if val is None else ""
        print(f"  {key:<30} {val}{unit}{note}")
    
    out_file = top.replace('.jpg', '_params.json').replace('.png', '_params.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nСохранено: {out_file}")
```

---

## Шаг 2В — Единая точка входа

### `analyze.py`

```python
import sys
import json
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python analyze.py hand_scan.ply")
        print("  python analyze.py top_view.jpg")
        print("  python analyze.py top_view.jpg side_view.jpg")
        sys.exit(1)
    
    first = sys.argv[1].lower()
    ext = Path(first).suffix.lower()
    
    if ext in ('.ply', '.obj'):
        from analyze_scan import analyze_hand_scan
        result = analyze_hand_scan(sys.argv[1])
        out_file = sys.argv[1].replace(ext, '_params.json')
        
    elif ext in ('.jpg', '.jpeg', '.png'):
        from analyze_photo import analyze_hand_photo
        side = sys.argv[2] if len(sys.argv) > 2 else None
        result = analyze_hand_photo(sys.argv[1], side)
        out_file = sys.argv[1].replace(ext, '_params.json')
        
    else:
        print(f"Неподдерживаемый формат: {ext}")
        print("Поддерживается: .ply .obj .jpg .jpeg .png")
        sys.exit(1)
    
    # Единый вывод
    print("\n" + "="*50)
    print("ПАРАМЕТРЫ → FreeCAD")
    print("="*50)
    params = result['grip_params']
    for key, val in params.items():
        if val is not None:
            print(f"  {key:<30} {val}")
    
    if result.get('accuracy_note'):
        print(f"\n  Точность: {result['accuracy_note']}")
    
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nСохранено: {out_file}")

if __name__ == '__main__':
    main()
```

---

## Шаг 3 — FreeCAD: параметрический скелет

### Структура файла FreeCAD

```
grip_skeleton.FCStd
├── Spreadsheet (биометрические параметры)
├── Sketcher
│   ├── Sketch_Wrist      — сечение запястье
│   ├── Sketch_PalmLow    — сечение нижняя ладонь
│   ├── Sketch_PalmMid    — сечение середина (palm swell)
│   ├── Sketch_PalmHigh   — сечение верхняя ладонь
│   └── Sketch_Fingers    — сечение под пальцы
└── Part Design
    └── Loft (через все сечения)
```

### Spreadsheet — переменные

```
# Биометрия (из grip_params JSON)
palm_width          = 87.0   # мм
palm_length         = 112.0  # мм
palm_depth          = 28.0   # мм
grip_thickness      = 23.9   # мм (grip_thickness_rec)
palm_swell_y_pct    = 52.0   # %
wrist_width         = 71.0   # мм
grip_height         = 68.0   # мм
trigger_reach       = 55.0   # мм

# Монтаж FWB 800X (фиксированные!)
fwb_screw_1_x       = 0.0    # мм (центр)
fwb_screw_1_y       = 15.0   # мм от низа
fwb_screw_2_y       = 45.0   # мм от низа
fwb_screw_dia       = 4.0    # мм (M4)
fwb_rail_width      = 18.0   # мм (уточнить с оригинала!)
fwb_rail_depth      = 6.0    # мм

# Параметры рукоятки
thumb_shelf_angle   = 15.0   # градусов
thumb_shelf_depth   = 8.0    # мм
pinky_shelf_h       = 5.0    # мм
backstrap_radius    = 35.0   # мм
```

### FreeCAD Python API — загрузка параметров из JSON

```python
# Запускать из FreeCAD Python Console
# или как макрос: Macro → Macros → New

import FreeCAD
import json

def load_params_to_spreadsheet(json_file, doc_name="grip_skeleton"):
    """Загружает параметры из JSON в Spreadsheet FreeCAD."""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    params = data['grip_params']
    
    doc = FreeCAD.getDocument(doc_name)
    sheet = doc.getObject("Spreadsheet")
    
    # Маппинг JSON → ячейки Spreadsheet
    mapping = {
        'palm_width_max':       'B1',
        'palm_length':          'B2',
        'palm_depth_max':       'B3',
        'grip_thickness_rec':   'B4',
        'palm_swell_y_pct':     'B5',
        'wrist_width':          'B6',
        'grip_height':          'B7',
        'trigger_reach_est':    'B8',
    }
    
    for param_key, cell in mapping.items():
        if param_key in params:
            sheet.set(cell, str(params[param_key]))
            print(f"  {cell}: {param_key} = {params[param_key]}")
    
    sheet.recompute()
    doc.recompute()
    FreeCAD.Console.PrintMessage("Параметры загружены.\n")

# Запуск
load_params_to_spreadsheet("/path/to/hand_scan_params.json")
```

### Референс сечений для Loft

```
Wrist section:
  width = Spreadsheet.wrist_width
  depth = Spreadsheet.grip_thickness * 0.80
  corners_radius = 8мм

PalmLow section (25% высоты):
  width = Spreadsheet.palm_width_max * 0.90
  depth = Spreadsheet.grip_thickness * 0.90

PalmMid section (palm swell, ~50%):
  width = Spreadsheet.palm_width_max
  depth = Spreadsheet.grip_thickness
  # Максимальное сечение

PalmHigh section (75%):
  width = Spreadsheet.palm_width_max * 0.88
  depth = Spreadsheet.grip_thickness * 0.95

Fingers section (top):
  width = Spreadsheet.width_at_fingers
  depth = Spreadsheet.grip_thickness * 0.85
```

### Экспорт из FreeCAD

```python
import FreeCAD
import Import

doc = FreeCAD.ActiveDocument
shape = doc.getObject("Loft")  # или Body

# Экспорт STEP (для Fusion)
Import.export([shape], "/output/grip_skeleton.step")

# Опционально STL (для проверки)
import Mesh
Mesh.export([shape], "/output/grip_skeleton.stl")
```

---

## Шаг 4 — Fusion 360: органика и финальный solid

### Workflow в Fusion

```
1. File → Open → grip_skeleton.step
2. Проверить сечения (должны импортироваться как Wires)
3. Patch workspace → Loft через сечения
4. Sculpt (Form) workspace → T-Splines доводка:
   - thumb shelf органика
   - palm swell плавность
   - pinky groove
5. Solid workspace:
   - Shell (толщина стенок 2.5мм минимум)
   - Монтажные отверстия FWB (из параметров)
   - Fillet на острых краях (R2-4мм)
6. Export → STL / STEP
```

### Зоны для последующего Blender

```
SOLID зоны (не трогать в Blender):
  - Монтажная площадка FWB (верх)
  - Отверстия под винты ±5мм
  - Нижняя часть wrist (структурная)

LATTICE зоны (Voronoi в Blender):
  - Боковые панели grip (основной контакт ладони)
  - Thumb shelf поверхность
  - Задняя панель backstrap (опционально)
```

---

## Шаг 5 — Blender: Voronoi поверхность

### Зональная логика (voronoi_params.json)

Не один паттерн на всю рукоятку — зональная плотность:

```
Зона                  Scale   Плотность   Где
──────────────────────────────────────────────────────────
finger_contact        5.5     dense       пальцы + thenar
palm_contact          4.5     medium      основной контакт ладони
thumb_shelf           5.0     med-dense   упор большого пальца
backstrap_outer       3.0     open        тыльная сторона — max открытая
solid                 —       solid       монтаж FWB, отверстия ±6мм
```

**Рёбра — минимум 5мм, сечение овальное (aspect ratio 1.6):**
Круглое ребро давит в точку — некомфортно при длительном хвате.
Овальное распределяет нагрузку по линии.

**Размер ячеек под размер руки:**
```
XXS: ×0.85  XS: ×0.90  S: ×0.95  M: ×1.00  L: ×1.05  XL: ×1.10
```

### Geometry Nodes — Voronoi shell

```
Нод-граф:
  
  Group Input (Geometry)
      ↓
  Named Attribute (zone_id) → маска зоны
      ↓
  Mesh to Points (распределение точек на поверхности)
      ↓
  Voronoi Texture (Randomness=0.75, Scale=per_zone)
      ↓
  [Map Range] порог → маска ячеек
      ↓
  Delete Geometry (удаляем грани по маске)
      ↓
  Solidify (Thickness = 1.8мм, oval cross-section)
      ↓
  Subdivision (уровень 1)
      ↓
  Group Output
```

### Blender Python — Solidify и экспорт

```python
import bpy

obj = bpy.context.active_object

# Solidify modifier
mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
mod.thickness = 0.0018  # 1.8мм в метрах (Blender единицы)
mod.offset = -1.0       # внутрь

# Apply и экспорт STL
bpy.ops.object.modifier_apply(modifier="Solidify")

bpy.ops.export_mesh.stl(
    filepath="/output/grip_final.stl",
    use_selection=True,
    global_scale=1000.0,  # Blender метры → мм для слайсера
)
```

### Маскирование зон (solid vs lattice)

```python
# Vertex Groups для разделения зон
# Grip zone (Voronoi) — группа "grip_zone"
# Mounting zone (solid) — группа "solid_zone"

# Geometry Nodes использует Named Attribute
# чтобы применять Voronoi только на grip_zone
# Scale берётся из voronoi_params.json по grip_size
```

---

## Шаг 6 — Слайсер и печать

### Рекомендации по материалу

| Материал | Плюсы | Минусы | Для чего |
|---|---|---|---|
| PA12 (нейлон) | Гибкость, прочность, SLS | Дорогой, нужен SLS принтер | Финальная рукоятка |
| PETG | Баланс цена/качество | Менее прочный | Прототипы 2-3 |
| PLA CF | Жёсткость, вид | Хрупкий | Только для показа |
| ASA | UV стойкость | Усадка | Внешние части |

### Параметры печати (PETG прототип)

```
Layer height:     0.15мм
Wall loops:       4
Infill:           30% Gyroid
Supports:         Tree, only from bed
Bed temp:         70°C
Nozzle temp:      240°C
```

### Минимальные толщины для Voronoi зон

```
Перемычки Voronoi:    ≥ 1.5мм
Solid стенки:         ≥ 2.5мм
Mounting area:        ≥ 4.0мм (solid, без решётки)
```

---

## Итоговый Pipeline (команды)

```bash
# 1А. Анализ скана
python analyze.py hand_scan.ply
# → hand_scan_params.json

# 1Б. Анализ фото (1 ракурс)
python analyze.py top_view.jpg
# → top_view_params.json

# 1Б. Анализ фото (2 ракурса — рекомендуется)
python analyze.py top_view.jpg side_view.jpg
# → top_view_params.json

# 2. FreeCAD (GUI или headless)
# Загрузить grip_skeleton.FCStd
# Запустить макрос load_params_to_spreadsheet()
# Экспортировать grip_skeleton.step

# 3. Fusion 360 (GUI)
# Импорт STEP → Loft → T-Splines → STEP/STL

# 4. Blender (GUI или python -b)
# Импорт STL → Geometry Nodes Voronoi → Экспорт STL

# 5. Слайсер → Gcode → Печать
```

---

## Файловая структура проекта

```
grip_project/
├── input/
│   ├── hand_scan.ply           # скан руки (если есть)
│   ├── top_view.jpg            # фото сверху
│   ├── side_view.jpg           # фото сбоку
│   └── *_params.json           # выход analyze.py
├── freecad/
│   └── grip_skeleton.FCStd     # параметрический скелет
├── fusion/
│   └── grip_solid.step         # органический solid
├── blender/
│   ├── grip_voronoi.blend      # проект Blender
│   └── grip_final.stl          # финальный STL
├── scripts/
│   ├── analyze.py              # единая точка входа
│   ├── analyze_scan.py         # анализ PLY/OBJ
│   ├── analyze_photo.py        # анализ фото + рамка
│   └── freecad_load_params.py  # загрузка в FreeCAD
└── output/
    └── grip_print_ready.stl    # для слайсера
```

---

## TODO / Итерации

- [ ] Снять точные размеры монтажа FWB 800X (fwb_rail_width, fwb_screw_*)
- [ ] Первый прототип — plain solid без Voronoi (проверка посадки)
- [ ] Примерка → корректировка palm_swell_y_pct и thumb_shelf_angle
- [ ] Второй прототип — с Voronoi на боковых панелях
- [ ] Финал — PA12 SLS или многоматериальная печать

---

*Документ сгенерирован для Claude Code. Все размеры в мм если не указано иное.*
