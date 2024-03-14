from abc import ABC, abstractmethod
import pandas as pd
import re
import textdistance
from tqdm import tqdm


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





class RouteCalculator(ABC):
    @abstractmethod
    def calculate_routes(self, data: pd.DataFrame, MAX_TIME_BETWEEN_TRIPS: int) -> pd.DataFrame:
        pass

    @abstractmethod
    def adjust_routes(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

class SimpleRouteCalculator(RouteCalculator):
    def calculate_routes(self, data: pd.DataFrame, MAX_TIME_BETWEEN_TRIPS: int) -> pd.DataFrame:
        routes_info = []
        for num_plate, group in tqdm(data.groupby('num_plate'), desc="Calculating Routes"):
            current_trip = {'num_plate': num_plate, 'route': [], 'times': [], 'entry_date': None, 'exit_date': None, 'directions': []}
            prev_row = None

            for _, row in group.iterrows():
                if prev_row is not None:
                    time_diff = (row['date'] - prev_row['date']).total_seconds() / 60

                    if time_diff > MAX_TIME_BETWEEN_TRIPS
                        if current_trip['entry_date'] is not None:
                            current_trip['exit_date'] = prev_row['date']
                            routes_info.append(current_trip)
                        current_trip = {'num_plate': num_plate, 'route': [row['camera_ID']], 'times': [], 'entry_date': row['date'], 'exit_date': None, 'directions': [row['direction']]}

                if prev_row is not None:
                    current_trip['times'].append(time_diff)
                current_trip['route'].append(row['camera_ID'])
                current_trip['directions'].append(row['direction'])
                if current_trip['entry_date'] is None
                    current_trip['entry_date'] = row['date']

                prev_row = row

            if current_trip['entry_date'] is not None:
                current_trip['exit_date'] = prev_row['date'] if prev_row is not None else None
                if current_trip['exit_date'] is not None:
                    routes_info.append(current_trip)

        return pd.DataFrame(routes_info)

    def adjust_routes(self, data: pd.DataFrame, insertions) -> pd.DataFrame:
        refined_routes = []

        for index, row in data.iterrows():
            route, num_plate, times = row['route'], row['num_plate'], row.get('times', []),
            entry_date, exit_date = row['entry_date'], row['exit_date']

            refined_route = [route[0]]
            refined_times = []

            for i in range(1, len(route)):
                current_cam, prev_cam = route[i], route[i - 1]
                time_to_use = times[i - 1] if i - 1 < len(times) else 0

                if (prev_cam, current_cam) in insertions:
                    for insert_cam in insertions[(prev_cam, current_cam)]:
                        refined_route.append(insert_cam)
                        refined_times.append(time_to_use / (len(insertions[(prev_cam, current_cam)]) + 1))
                    refined_times.append(time_to_use / (len(insertions[(prev_cam, current_cam)]) + 1))
                else:
                    refined_route.append(current_cam)
                    refined_times.append(time_to_use)

            refined_routes.append({
                'num_plate': num_plate,
                'route': refined_route,
                'times': refined_times,
                'entry_date': entry_date,
                'exit_date': exit_date
            })

        return pd.DataFrame(refined_routes)



class DataProcessor:
    def __init__(self, filepath, corrector: Corrector, route_calculator: RouteCalculator):
        self.filepath = filepath
        self.corrector = corrector
        self.route_calculator = route_calculator
        self.data = None

    def load_and_prepare_data(self):
        self.data = pd.read_csv(self.filepath)
        self.data['date'] = pd.to_datetime(self.data['date'])
        self.data = self.data.iloc[:int(len(self.data) * 0.01)]
        self.data.sort_values(by=['num_plate', 'date'], inplace=True)

    def correct_num_plates_and_remove_hashes(self):
        self.data = self.corrector.correct_num_plates(self.data)
        self.data = self.data[~self.data['num_plate'].str.contains('#')]
        self.data = self.data[~(self.data['num_plate'] == 'unknown') & (self.data['num_plate'].str.len() > 3)]

    def calculate_and_adjust_routes(self, MAX_TIME_BETWEEN_TRIPS, insertions):
        self.data = self.route_calculator.calculate_routes(self.data, MAX_TIME_BETWEEN_TRIPS)
        self.data = self.route_calculator.adjust_routes(self.data, insertions)

    def verify_and_classify_visits(self):
        self.data['cumulative_entries'] = 1
        self.data.sort_values(by=['num_plate', 'entry_date'], inplace=True)
        self.data['cumulative_entries'] = self.data.groupby('num_plate').cumcount() + 1
