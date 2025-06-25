# extractor/trajectory_builder.py
"""
TrajectoryBuilder 모듈

- 각 문자 마스크로부터 skeleton을 추출하고,
- 경로(path) 단위로 분리한 후,
- z-profile (두께 기반 높이값)을 계산하여
- pandas DataFrame 형식으로 반환하는 역할을 수행합니다.

핵심 구성:
- PathAnalyzer: 각 경로 점의 두께를 측정하고 Z값으로 정규화
- TrajectoryBuilder: 전체 경로 생성 및 필터링, 방향 정렬 등 수행
"""

import pandas as pd
from .image_preprocessor import ImagePreprocessor
from .utils import (
    filter_nearby_points,
    flip_path_to_start_near_origin,
    get_local_thickness,
    normalize_thickness,
    path_to_dataframe,
)
from .skeleton_dfs_base import extract_all_paths

class PathAnalyzer:
    """
    주어진 마스크에서 (x, y) 좌표 기반으로 두께(thickness)를 측정하고
    Z 축 값으로 정규화하는 도구 클래스
    """
    def __init__(self, mask, z_min=0.5, z_max=3.0):
        self.mask = mask
        self.z_min = z_min
        self.z_max = z_max

    def get_thickness(self, x, y):
        """
        주어진 좌표에서 상하좌우로 퍼지면서 획의 두께를 측정함
        """
        return get_local_thickness(y, x, self.mask)

    def compute_z_profile(self, path):
        """
        path 상의 각 점에서 두께를 측정하고 z_min~z_max로 정규화한 Z값 배열 생성
        """
        thicknesses = [self.get_thickness(x, y) for x, y in path]
        return normalize_thickness(thicknesses, self.z_min, self.z_max)

class TrajectoryBuilder:
    """
    각 문자 마스크에 대해 skeleton 추출, 경로 분할, 방향 정렬, z-profile 부여까지
    경로 데이터를 생성하는 핵심 클래스
    """
    def __init__(self, skeleton_mode='skeletonize', z_min=0.5, z_max=3.0):
        self.skeleton_mode = skeleton_mode
        self.z_min = z_min
        self.z_max = z_max

    def build_trajectories(self, idx, mask):
        """
        주어진 문자 마스크로부터 중심선(skeleton)을 추출하고,
        각 경로(path)에 대해 z-profile을 계산하여 DataFrame 리스트 반환

        Args:
            idx (int): 문자 인덱스 (char_idx)
            mask (np.ndarray): 단일 문자의 이진 마스크

        Returns:
            list of pd.DataFrame: 각 path에 대한 trajectory 정보
        """
        # skeleton 추출 (binary mask 기준)
        skel = ImagePreprocessor.extract_skeleton_from_mask(mask, self.skeleton_mode)
        if skel is None or skel.sum() < 10:
            return []

        # skeleton에서 DFS 기반 경로 추출
        paths = extract_all_paths(skel)
        analyzer = PathAnalyzer(mask, self.z_min, self.z_max)
        dataframes = []

        for path in paths:
            # 점 사이 간격 필터링
            path = filter_nearby_points(path, min_dist=2.0)
            if not path:
                continue
            # 시작점 정렬 (x좌표 기준 좌측에서 시작)
            path = flip_path_to_start_near_origin(path)
            # 두께 → z-profile 계산
            z_profile = analyzer.compute_z_profile(path)
            # DataFrame 생성 (char_idx, x, y, z)
            df = path_to_dataframe(path, z_profile, char_idx=idx)
            dataframes.append(df)

        return dataframes
