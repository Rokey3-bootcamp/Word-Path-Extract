# extractor/contour_extractor.py
"""
CharacterContourExtractor 모듈

입력된 이진 이미지에서 문자(또는 객체)의 외곽선을 추출하고,
각 객체마다 개별적인 마스크를 생성하는 기능을 담당합니다.

활용 위치:
- 이미지 전처리 후 각 문자의 중심선을 추출하기 전에 사용됨
- 각 문자를 독립적인 이진 마스크로 분리해 downstream 처리 가능하게 함

특징:
- OpenCV의 findContours + RETR_CCOMP 방식을 사용
- 계층 구조를 고려해 외부 contour만 필터링 (자식 contour 제외)
"""

import cv2
import numpy as np

class CharacterContourExtractor:
    """
    이진 이미지에서 문자 또는 닫힌 외곽선들을 추출하여,
    개별 객체 마스크(binary mask)를 생성하는 클래스
    """
    def __init__(self, binary_img):
        """
        Args:
            binary_img (np.ndarray): 이진화된 입력 이미지 (0 또는 1)
        """
        self.binary = binary_img
        self.contours, self.hierarchy = self._find_external_contours()

    def _find_external_contours(self):
        """
        OpenCV를 사용해 외곽선과 계층 구조 추출

        Returns:
            contours (list): contour 좌표 리스트
            hierarchy (list): contour 간 관계 구조 (부모-자식)
        """
        contours, hierarchy = cv2.findContours(
            self.binary.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )
        return contours, hierarchy[0] if hierarchy is not None else []

    def get_character_masks(self):
        """
        외부 contour만 필터링하여 문자 마스크를 생성하고 반복자로 반환

        Yields:
            idx (int): contour 인덱스 (문자 번호)
            mask (np.ndarray): 해당 문자만 True인 이진 마스크
        """
        for idx, cnt in enumerate(self.contours):
            # 부모 contour만 사용 (hierarchy[i][3] == -1)
            if len(self.hierarchy) == 0 or self.hierarchy[idx][3] != -1:
                continue

            # contour를 채운 mask 생성
            mask = np.zeros_like(self.binary)
            cv2.drawContours(mask, [cnt], -1, 1, thickness=-1)
            yield idx, mask
