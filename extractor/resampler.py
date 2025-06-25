# extractor/resampler.py
"""
resampler 모듈

입력된 경로 DataFrame을 등간격으로 보간하고,
경로 상의 거리 차이가 너무 큰 경우 해당 경로를 분할하는 기능을 제공합니다.

주요 기능:
- 일정 거리로 경로를 보간하여 샘플링 수를 맞춤
- max_gap 이상 떨어진 점은 다른 path로 분리하여 연속성 보장

사용 위치:
- MultiCharacterTrajectoryExtractor.get_all_dataframes_resampled()
"""

import numpy as np
import pandas as pd

def resample_path(df, n_points, max_gap=10.0):
    """
    주어진 경로 DataFrame(df)을 등간격으로 n_points만큼 샘플링하고,
    max_gap 이상의 간격이 발생하면 별도 path로 분할합니다.

    Args:
        df (pd.DataFrame): 하나의 문자 경로를 담은 DataFrame
        n_points (int): 샘플링할 점의 개수
        max_gap (float): 두 샘플링 점 간 거리로 경로 분할 기준

    Returns:
        list of pd.DataFrame: 샘플링되고 분할된 경로들의 리스트
    """
    xs = df['x'].to_numpy()
    ys = df['y'].to_numpy()
    zs = df['z'].to_numpy()
    char_idx = df['char_idx'].iloc[0]

    if len(xs) < 2 or n_points < 2:
        return [df]  # 보간할 수 없는 경우 원본 반환

    # 각 점 간 거리 누적합 계산
    deltas = np.sqrt(np.diff(xs)**2 + np.diff(ys)**2)
    s = np.concatenate([[0], np.cumsum(deltas)])
    total_len = s[-1]

    # 보간 기준이 되는 등간격 거리 배열 생성
    target_s = np.linspace(0, total_len, n_points)

    # 각 보간 기준에 대해 가장 가까운 실제 인덱스 선택
    indices = []
    prev_idx = -1
    for ts in target_s:
        idx = np.argmin(np.abs(s - ts))
        if idx != prev_idx:
            indices.append(idx)
            prev_idx = idx

    # max_gap 기준으로 경로 분할 지점 계산
    split_indices = [0]
    for i in range(1, len(indices)):
        prev = indices[i-1]
        curr = indices[i]
        dist = np.hypot(xs[curr] - xs[prev], ys[curr] - ys[prev])
        if dist > max_gap:
            split_indices.append(i)

    # 분할된 구간을 각각 DataFrame으로 생성
    result_paths = []
    for si, ei in zip(split_indices, split_indices[1:] + [len(indices)]):
        idxs = indices[si:ei]
        if len(idxs) < 2:
            continue  # 너무 짧은 path는 무시
        xs_new = xs[idxs]
        ys_new = ys[idxs]
        zs_new = zs[idxs]
        df_new = pd.DataFrame({
            'char_idx': char_idx,
            'x': xs_new,
            'y': ys_new,
            'z': zs_new
        })
        result_paths.append(df_new)

    return result_paths
