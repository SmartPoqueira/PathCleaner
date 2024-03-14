from abc import ABC, abstractmethod
import pandas as pd
import re
from tqdm import tqdm
import textdistance

class Corrector(ABC):
    def __init__(self, normalize=False):
        self.normalize = normalize
        self.NON_ALPHANUMERIC = '[^a-z0-9]'
        self.non_alphanumeric_regex = re.compile(self.NON_ALPHANUMERIC)

    def correct_num_plates(self, data: pd.DataFrame) -> pd.DataFrame:
        plates_with_non_alphanumeric = data[data['num_plate'].apply(lambda x: bool(self.non_alphanumeric_regex.search(x.lower())))]['num_plate'].unique()
        plates_without_non_alphanumeric = data[~data['num_plate'].apply(lambda x: bool(self.non_alphanumeric_regex.search(x.lower())))]['num_plate'].unique()
        correction_map = {}

        for plate_with_non_alphanumeric in tqdm(plates_with_non_alphanumeric, desc="Correcting Plates"):
            if self.normalize:
                plate_with_non_alphanumeric = self.normalize_plate(plate_with_non_alphanumeric)
            min_distance = float('inf')
            best_match_plate = None

            for plate_without_non_alphanumeric in plates_without_non_alphanumeric:
                if self.normalize:
                    plate_without_non_alphanumeric = self.normalize_plate(plate_without_non_alphanumeric)
                distance = self.calculate_distance(plate_with_non_alphanumeric, plate_without_non_alphanumeric)
                if distance < min_distance:
                    min_distance = distance
                    best_match_plate = plate_without_non_alphanumeric

            non_alphanumeric_count = len(self.non_alphanumeric_regex.findall(plate_with_non_alphanumeric))
            if min_distance <= non_alphanumeric_count:
                correction_map[plate_with_non_alphanumeric] = best_match_plate

        for plate_with_non_alphanumeric, plate_corrected in correction_map.items():
            data.loc[data['num_plate'] == plate_with_non_alphanumeric, 'num_plate'] = plate_corrected

        return data

    def normalize_plate(self, plate: str) -> str:
        normalized_plate = self.non_alphanumeric_regex.sub('', plate.lower())
        return normalized_plate

    @abstractmethod
    def calculate_distance(self, plate_with_non_alphanumeric, plate_without_non_alphanumeric) -> int:
        pass

class DamerauLevenshteinCorrector(Corrector):
    def calculate_distance(self, plate_with_non_alphanumeric, plate_without_non_alphanumeric) -> int:
        return textdistance.damerau_levenshtein(plate_with_non_alphanumeric, plate_without_non_alphanumeric)

class LevenshteinCorrector(Corrector):
    def calculate_distance(self, plate_with_non_alphanumeric, plate_without_non_alphanumeric) -> int:
        return textdistance.levenshtein(plate_with_non_alphanumeric, plate_without_non_alphanumeric)
