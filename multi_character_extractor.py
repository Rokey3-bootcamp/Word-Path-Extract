# extractor/multi_character_extractor.py
"""
MultiCharacterTrajectoryExtractor 모듈

이 모듈은 단일 이미지에서 여러 문자 또는 도형을 인식하고,
각 문자마다 중심선을 따라 등간격 경로를 생성하는 기능을 제공합니다.

전체 파이프라인 흐름:
1. 이미지 로딩 및 이진화
2. 외곽선 기반 문자 분리 (contour extraction)
3. 각 문자에 대해 skeleton을 추출하여 path 생성
4. z-profile (획 두께 기반 높이값) 계산
5. 등간격 보간 및 분할 처리
6. DataFrame 리스트 반환
"""

import cv2
from extractor.image_preprocessor import ImagePreprocessor
from extractor.contour_extractor import CharacterContourExtractor
from extractor.trajectory_builder import TrajectoryBuilder
from extractor.resampler import resample_path
from itertools import chain

class MultiCharacterTrajectoryExtractor:
    """
    여러 문자 또는 도형이 포함된 이미지를 입력으로 받아,
    각 객체의 중심선을 기반으로 3D trajectory를 추출하는 클래스
    """
    def __init__(self, img_path, z_min=0.5, z_max=3.0, skeleton_mode='skeletonize'):
        """
        초기화 함수

        Args:
            img_path (str): 입력 이미지 경로 (grayscale 예상)
            z_min (float): 획 최소 두께일 때의 Z값
            z_max (float): 획 최대 두께일 때의 Z값
            skeleton_mode (str): skeleton 추출 방식 ('skeletonize', 'stroke' 등)
        """
        self.img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if self.img is None:
            raise FileNotFoundError(f'이미지 경로 오류: {img_path}')

        # 이진화 이미지 저장
        self.binary = ImagePreprocessor(self.img).binary

        # 중심선 경로 추출기 초기화
        self.builder = TrajectoryBuilder(skeleton_mode, z_min, z_max)

        # 전체 문자들의 DataFrame 리스트 생성
        self.char_dataframes = self._extract_all()

    def _extract_all(self):
        """
        내부용 함수: 이진화 이미지에서 모든 문자 경로를 추출

        Returns:
            list of pd.DataFrame: 각 문자마다 (x, y, z, char_idx) 포함한 DataFrame
        """
        extractor = CharacterContourExtractor(self.binary)
        all_dfs = []

        for idx, mask in extractor.get_character_masks():
            # 문자 하나당 여러 경로가 생길 수 있음
            dfs = self.builder.build_trajectories(idx, mask)
            all_dfs.extend(dfs)

        return all_dfs

    def get_all_dataframes(self):
        """
        모든 문자 경로의 원본 DataFrame 리스트 반환

        Returns:
            list of pd.DataFrame
        """
        return self.char_dataframes

    def get_all_dataframes_resampled(self, n_points, max_gap=20.0):
        """
        각 문자 경로를 등간격 보간하고, 최대 간격 기준으로 분할

        Args:
            n_points (int): 보간 후 포인트 수
            max_gap (float): 두 점 사이 간격이 이 값을 넘으면 분할

        Returns:
            list of pd.DataFrame: 보간 및 분할된 결과 리스트
        """
        resampled_nested = [resample_path(df, n_points, max_gap) for df in self.char_dataframes]
        return list(chain.from_iterable(resampled_nested))


if __name__ == '__main__':
    import sys
    import pandas as pd

    # 커맨드라인 인자로 이미지 경로 받기
    img_path = sys.argv[1]

    # 추출기 인스턴스 생성
    extractor = MultiCharacterTrajectoryExtractor(
        img_path=img_path,
        z_min=0.5,
        z_max=3.0,
        skeleton_mode='stroke'  # 윤곽선을 두껍게 그려 skeleton 추출
    )

    # 보간 및 경로 분할
    all_dfs = extractor.get_all_dataframes_resampled(n_points=30, max_gap=15.0)

    # 경로별 요약 출력
    for i, df in enumerate(all_dfs):
        print(f"--- Path {i} ---")
        print(df.head())
