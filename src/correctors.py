from abc import ABC, abstractmethod
import pandas as pd
import re
from tqdm import tqdm
import textdistance


class Corrector(ABC):
    def __init__(self, normalize=False):
        self.normalize = normalize

    def correct_num_plates(self, data: pd.DataFrame) -> pd.DataFrame:
        plates_with_hash = data[data['num_plate'].str.contains('#')]['num_plate'].unique()
        plates_without_hash = data[~data['num_plate'].str.contains('#')]['num_plate'].unique()
        correction_map = {}

        for plate_with_hash in tqdm(plates_with_hash, desc="Correcting Plates with Hashes"):
            if self.normalize:
                plate_with_hash = self.normalize_plate(plate_with_hash)
            min_distance = float('inf')
            best_match_plate = None

            for plate_without_hash in plates_without_hash:
                if self.normalize:
                    plate_without_hash = self.normalize_plate(plate_without_hash)
                distance = self.calculate_distance(plate_with_hash, plate_without_hash)
                if distance < min_distance:
                    min_distance = distance
                    best_match_plate = plate_without_hash

            if min_distance <= plate_with_hash.count('#'):
                correction_map[plate_with_hash] = best_match_plate

        for plate_with_hash, plate_corrected in correction_map.items():
            data.loc[data['num_plate'] == plate_with_hash, 'num_plate'] = plate_corrected

        return data

    def normalize_plate(self, plate: str) -> str:
        normalized_plate = re.sub('[^a-zA-Z0-9]', '', plate).lower()
        return normalized_plate

    @abstractmethod
    def calculate_distance(self, plate_with_hash, plate_without_hash) -> int:
        pass

class DamerauLevenshteinCorrector(Corrector):
    def calculate_distance(self, plate_with_hash, plate_without_hash) -> int:
        return textdistance.damerau_levenshtein(plate_with_hash, plate_without_hash)

class LevenshteinCorrector(Corrector):
    def calculate_distance(self, plate_with_hash, plate_without_hash) -> int:
        return textdistance.levenshtein(plate_with_hash, plate_without_hash)
