# extractor/image_preprocessor.py
"""
ImagePreprocessor 모듈

이미지를 이진화(binarization)하고 skeleton(중심선)을 추출하는 전처리 단계를 담당합니다.

주요 기능:
- binarize(): Otsu 알고리즘을 이용한 자동 이진화
- extract_skeleton_from_mask(): 다양한 방식의 skeleton 또는 윤곽선 추출

지원하는 skeleton 모드:
- 'skeletonize': 일반적인 중심선 추출 (얇고 정확함)
- 'medial': 거리 기반 중심선 (medial axis transform)
- 'outer': 외곽선을 두껍게 그려 윤곽선을 skeleton처럼 사용
- 'stroke': 획을 굵게 채워 skeletonize (붓글씨 획 느낌)
"""

import cv2
from skimage.morphology import skeletonize, medial_axis
import numpy as np

class ImagePreprocessor:
    """
    이미지 전처리 클래스
    - 초기화 시 입력 이미지를 이진화하여 self.binary로 저장
    - 객체 내부 이진 마스크를 기반으로 skeleton 추출 가능
    """
    def __init__(self, img: np.ndarray):
        """
        Args:
            img (np.ndarray): 입력 이미지 (grayscale)
        """
        self.gray = img
        self.binary = self.binarize(img)

    @staticmethod
    def binarize(img):
        """
        Otsu 알고리즘을 이용하여 이미지를 자동 이진화 (0 또는 1로 구성)

        Returns:
            np.ndarray: 이진 마스크 이미지
        """
        _, binary = cv2.threshold(img, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binary

    def extract_skeleton(self, mode='skeletonize'):
        """
        인스턴스 내부의 self.binary 마스크에서 skeleton 추출

        Returns:
            np.ndarray: skeleton 마스크
        """
        return self.extract_skeleton_from_mask(self.binary, mode)

    @staticmethod
    def extract_skeleton_from_mask(mask, mode='skeletonize'):
        """
        주어진 binary mask로부터 중심선 또는 윤곽선을 추출

        Args:
            mask (np.ndarray): binary image (0 또는 1)
            mode (str): 추출 방식

        Returns:
            np.ndarray: skeleton 또는 윤곽선 마스크
        """
        if mode == 'skeletonize':
            # 일반적인 중심선 추출 (얇고 세밀함)
            return skeletonize(mask > 0).astype(np.uint8)

        elif mode == 'medial':
            # 거리 기반 중심선 추출 (비교적 부드럽고 두꺼움)
            medial, _ = medial_axis(mask > 0, return_distance=True)
            return medial.astype(np.uint8)

        elif mode == 'outer':
            # 외곽선만 추출하여 윤곽을 굵게 그림 (contour 기반)
            contours, hierarchy = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            if hierarchy is None:
                return np.zeros_like(mask)

            skeleton_like = np.zeros_like(mask)
            hierarchy = hierarchy[0]
            for i, cnt in enumerate(contours):
                if hierarchy[i][3] == -1:  # 최상위 contour만 사용
                    cv2.drawContours(skeleton_like, [cnt], -1, 1, thickness=7)
            return skeleton_like

        elif mode == 'stroke':
            # 외곽선을 굵게 그린 뒤 skeletonize하여 획처럼 처리
            filled = np.zeros_like(mask)
            contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(filled, contours, -1, 1, thickness=5)
            skeleton = skeletonize(filled > 0).astype(np.uint8)
            return skeleton

        else:
            raise ValueError(f"Unknown skeleton mode: {mode}")
