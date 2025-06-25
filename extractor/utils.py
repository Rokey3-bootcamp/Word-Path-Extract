# extractor/utils.py
"""
utils 모듈

skeleton에서 추출한 경로(path)를 후처리하기 위한 유틸리티 함수들을 포함합니다.

기능:
- 인접 점 필터링 (거리 기준)
- 경로 방향 정렬 (x=0에 가까운 쪽을 시작점으로)
- 각 점에서의 두께 측정 및 정규화
- DataFrame으로 변환

이 함수들은 TrajectoryBuilder 내부에서 주로 사용됩니다.
"""

import numpy as np
import pandas as pd

def filter_nearby_points(path, min_dist=2.0):
    """
    경로 상에서 너무 가까운 점들을 제거하여 간결한 경로로 만듦

    Args:
        path (list of (x, y)): 원본 경로 좌표 리스트
        min_dist (float): 최소 유지할 거리 (픽셀 단위)

    Returns:
        list of (x, y): 필터링된 경로
    """
    if not path:
        return path
    filtered = [path[0]]
    for pt in path[1:]:
        prev = filtered[-1]
        if np.hypot(pt[0] - prev[0], pt[1] - prev[1]) >= min_dist:
            filtered.append(pt)
    return filtered

def flip_path_to_start_near_origin(path):
    """
    경로의 시작점이 좌측(x=0)에 가까운 쪽이 되도록 방향을 뒤집음

    Args:
        path (list of (x, y))

    Returns:
        list of (x, y): 앞뒤가 정렬된 경로
    """
    if not path or len(path) < 2:
        return path
    x0 = abs(path[0][0])
    x1 = abs(path[-1][0])
    return path if x0 <= x1 else path[::-1]

def get_local_thickness(y, x, binary, max_search=30):
    """
    주어진 위치에서 상하좌우 방향으로 확장하면서 획의 두께를 측정

    Args:
        y, x (int): 기준 좌표
        binary (np.ndarray): binary mask
        max_search (int): 최대 탐색 길이

    Returns:
        int: 해당 점에서의 근사 획 두께
    """
    H, W = binary.shape
    dists = []
    for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:  # 상하좌우
        cnt = 0
        ny, nx = y+dy, x+dx
        while 0 <= ny < H and 0 <= nx < W and binary[ny, nx]:
            cnt += 1
            ny += dy
            nx += dx
            if cnt > max_search:
                break
        dists.append(cnt)
    return sum(dists)

def normalize_thickness(thicknesses, z_min, z_max):
    """
    두께값을 z_min ~ z_max 범위로 선형 정규화

    Args:
        thicknesses (list of int): 원본 두께 리스트
        z_min, z_max (float): 정규화 범위

    Returns:
        np.ndarray: 정규화된 z값
    """
    thicknesses = np.array(thicknesses)
    if thicknesses.ptp() == 0:  # 두께 변화가 없을 경우
        return np.full_like(thicknesses, z_min, dtype=float)
    else:
        return z_min + (thicknesses - thicknesses.min()) / (thicknesses.ptp() + 1e-6) * (z_max - z_min)

def path_to_dataframe(path, z_profile, char_idx):
    """
    (x, y, z) 정보를 pandas DataFrame으로 변환

    Args:
        path (list of (x, y)): 경로 좌표
        z_profile (list of float): 각 점의 z값 (정규화된 두께)
        char_idx (int): 문자 인덱스

    Returns:
        pd.DataFrame: columns=['char_idx', 'x', 'y', 'z']
    """
    xs, ys = zip(*path)
    return pd.DataFrame({
        'char_idx': char_idx,
        'x': xs,
        'y': ys,
        'z': z_profile
    })
