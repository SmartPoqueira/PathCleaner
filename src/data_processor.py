import pandas as pd
from correctors import Corrector, LevenshteinCorrector, DamerauLevenshteinCorrector
from route_calculators import RouteCalculator, SimpleRouteCalculator

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
        self.data = self.data[~self.data['num_plate'].str.lower().str.contains('[^a-z0-9]', regex=True)]
        self.data = self.data[~(self.data['num_plate'] == 'unknown') & (self.data['num_plate'].str.len() > 3)]

    def calculate_and_adjust_routes(self, MAX_TIME_BETWEEN_TRIPS, insertions):
        self.data = self.route_calculator.calculate_routes(self.data, MAX_TIME_BETWEEN_TRIPS)
        self.data = self.route_calculator.adjust_routes(self.data, insertions)

    def verify_and_classify_visits(self):
        self.data.sort_values(by=['num_plate', 'entry_date'], inplace=True)
