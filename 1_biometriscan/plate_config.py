#!/usr/bin/env python3
"""
plate_config.py — ChArUco plate registry and interactive selection.

Known plates are defined in calibration/plates.json.
At runtime, a plate is selected via name (from CLI) or interactive prompt.

Usage:
    from plate_config import select_plate

    plate = select_plate()                  # interactive
    plate = select_plate('7x9_30mm')        # by name, no prompt
    board = plate.build_board()             # cv2.aruco.CharucoBoard
"""

import json
import cv2
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REGISTRY_PATH = Path(__file__).parent / 'calibration' / 'plates.json'

ARUCO_DICTS = {
    'DICT_4X4_50':   cv2.aruco.DICT_4X4_50,
    'DICT_4X4_100':  cv2.aruco.DICT_4X4_100,
    'DICT_4X4_250':  cv2.aruco.DICT_4X4_250,
    'DICT_4X4_1000': cv2.aruco.DICT_4X4_1000,
    'DICT_5X5_50':   cv2.aruco.DICT_5X5_50,
    'DICT_5X5_100':  cv2.aruco.DICT_5X5_100,
    'DICT_5X5_250':  cv2.aruco.DICT_5X5_250,
    'DICT_6X6_250':  cv2.aruco.DICT_6X6_250,
}


@dataclass
class PlateConfig:
    name: str
    description: str
    squares_x: int
    squares_y: int
    square_mm: float
    marker_mm: float
    aruco_dict: str = 'DICT_4X4_250'
    # Physical Y from the top edge of the board (ruler measurement on the printed plate).
    # To convert to _world_corners space: world_y = wrist_baseline_y_mm - square_mm
    wrist_baseline_y_mm: Optional[float] = None
    file: Optional[str] = None
    inverted: bool = False

    def build_board(self, mirrored: bool = False) -> cv2.aruco.CharucoBoard:
        aruco = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[self.aruco_dict])
        if mirrored:
            ids = self._mirrored_ids()
            return cv2.aruco.CharucoBoard(
                (self.squares_x, self.squares_y),
                self.square_mm / 1000.0,
                self.marker_mm / 1000.0,
                aruco,
                ids,
            )
        return cv2.aruco.CharucoBoard(
            (self.squares_x, self.squares_y),
            self.square_mm / 1000.0,
            self.marker_mm / 1000.0,
            aruco,
        )

    def _mirrored_id_to_pos(self) -> dict:
        """Return {marker_id: (col, row)} board position for the mirrored board."""
        ids = self._mirrored_ids()
        result = {}
        idx = 0
        for row in range(self.squares_y):
            for col in range(self.squares_x):
                if (col + row) % 2 == 1:
                    result[int(ids[idx])] = (col, row)
                    idx += 1
        return result

    def _mirrored_ids(self) -> np.ndarray:
        """Marker IDs with column order reversed per row (board printed mirrored horizontally)."""
        rows_ids = []
        marker_id = 0
        for row in range(self.squares_y):
            row_ids = []
            for col in range(self.squares_x):
                if (col + row) % 2 == 1:
                    row_ids.append(marker_id)
                    marker_id += 1
            rows_ids.append(row_ids)
        mirrored = []
        for row_ids in rows_ids:
            mirrored.extend(reversed(row_ids))
        return np.array(mirrored, dtype=np.int32)

    def summary(self) -> str:
        parts = [f"{self.squares_x}x{self.squares_y} grid, {self.square_mm}mm sq, {self.aruco_dict}"]
        if self.file:
            parts.append(f"file: {self.file}")
        if self.wrist_baseline_y_mm is not None:
            parts.append(f"wrist_y={self.wrist_baseline_y_mm}mm")
        return ' | '.join(parts)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'squares_x': self.squares_x,
            'squares_y': self.squares_y,
            'square_mm': self.square_mm,
            'marker_mm': self.marker_mm,
            'aruco_dict': self.aruco_dict,
            'wrist_baseline_y_mm': self.wrist_baseline_y_mm,
            'file': self.file,
        }


def load_registry() -> dict:
    with open(REGISTRY_PATH, encoding='utf-8') as f:
        return json.load(f)


def get_plate(name: str) -> PlateConfig:
    reg = load_registry()
    for p in reg['plates']:
        if p['name'] == name:
            return PlateConfig(**p)
    names = [p['name'] for p in reg['plates']]
    raise KeyError(f"Plate '{name}' not in registry. Available: {names}")


def list_plates() -> list[PlateConfig]:
    reg = load_registry()
    return [PlateConfig(**p) for p in reg['plates']]


def select_plate(plate_name: str = None) -> PlateConfig:
    """
    Return a PlateConfig.
    If plate_name is given, look it up in the registry (no prompt).
    Otherwise launch an interactive selection menu.
    """
    if plate_name is not None:
        return get_plate(plate_name)

    reg = load_registry()
    plates = reg['plates']
    default_name = reg.get('default', plates[0]['name'])

    print("\n--- ChArUco plate selection ---")
    for i, p in enumerate(plates, 1):
        marker = '*' if p['name'] == default_name else ' '
        cfg = PlateConfig(**p)
        print(f"  [{i}]{marker} {p['name']:<22} {p['description']}")
        print(f"      {cfg.summary()}")
    print(f"  [c]  Custom — enter parameters manually")
    print(f"  (* = default)")

    default_idx = next(
        (i + 1 for i, p in enumerate(plates) if p['name'] == default_name), 1
    )
    prompt = f"\nSelect [1-{len(plates)} / c] or Enter for default ({default_name}): "

    while True:
        raw = input(prompt).strip().lower()
        if raw == '':
            return PlateConfig(**next(p for p in plates if p['name'] == default_name))
        if raw == 'c':
            return _prompt_custom()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(plates):
                plate = PlateConfig(**plates[idx])
                print(f"  Selected: {plate.name}")
                return plate
        print(f"  Invalid input — enter 1-{len(plates)} or 'c'")


def _prompt_custom() -> PlateConfig:
    print("\nEnter custom plate parameters:")

    def ask_int(label, default):
        while True:
            raw = input(f"  {label} [{default}]: ").strip()
            if raw == '':
                return default
            try:
                return int(raw)
            except ValueError:
                print("    Integer required")

    def ask_float(label, default):
        while True:
            raw = input(f"  {label} [{default}]: ").strip()
            if raw == '':
                return default
            try:
                return float(raw)
            except ValueError:
                print("    Float required")

    squares_x = ask_int("squares_x (columns)", 7)
    squares_y = ask_int("squares_y (rows)", 9)
    square_mm = ask_float("square_mm (physical square size, mm)", 30.0)
    marker_mm = ask_float(f"marker_mm (≈70% of square, mm)", round(square_mm * 0.7, 1))

    print("\n  ArUco dictionary:")
    dict_names = list(ARUCO_DICTS.keys())
    for i, d in enumerate(dict_names, 1):
        marker = '*' if d == 'DICT_4X4_250' else ' '
        print(f"    [{i}]{marker} {d}")
    dict_idx = ask_int(f"  dictionary [1-{len(dict_names)}]", 3) - 1
    aruco_dict = dict_names[max(0, min(dict_idx, len(dict_names) - 1))]

    return PlateConfig(
        name='custom',
        description='User-defined custom plate',
        squares_x=squares_x,
        squares_y=squares_y,
        square_mm=square_mm,
        marker_mm=marker_mm,
        aruco_dict=aruco_dict,
        wrist_baseline_y_mm=None,
        file=None,
    )


def save_to_registry(plate: PlateConfig) -> None:
    """Append a new plate to plates.json (skips if name already exists)."""
    reg = load_registry()
    if any(p['name'] == plate.name for p in reg['plates']):
        print(f"  Plate '{plate.name}' already in registry — not overwriting")
        return
    reg['plates'].append(plate.to_dict())
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    print(f"  Saved '{plate.name}' to {REGISTRY_PATH}")


if __name__ == '__main__':
    plate = select_plate()
    print(f"\nPlate config:")
    print(f"  name:       {plate.name}")
    print(f"  grid:       {plate.squares_x}x{plate.squares_y}")
    print(f"  square_mm:  {plate.square_mm}")
    print(f"  marker_mm:  {plate.marker_mm}")
    print(f"  aruco_dict: {plate.aruco_dict}")
    if plate.wrist_baseline_y_mm is not None:
        print(f"  wrist_y:    {plate.wrist_baseline_y_mm}mm")
