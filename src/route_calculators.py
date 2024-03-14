from abc import ABC, abstractmethod
import pandas as pd
from tqdm import tqdm


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

                    if time_diff > MAX_TIME_BETWEEN_TRIPS:
                        if current_trip['entry_date'] is not None:
                            current_trip['exit_date'] = prev_row['date']
                            routes_info.append(current_trip)
                        current_trip = {'num_plate': num_plate, 'route': [row['camera_ID']], 'times': [], 'entry_date': row['date'], 'exit_date': None, 'directions': [row['direction']]}

                if prev_row is not None:
                    current_trip['times'].append(time_diff)
                current_trip['route'].append(row['camera_ID'])
                current_trip['directions'].append(row['direction'])
                if current_trip['entry_date'] is None:
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
