import pandas as pd
import json


def convert_plate_to_graphs_json(csv_path, plate, json_output_path):
    df = pd.read_csv(csv_path)
    print(df.columns)
    matching_rows = df[df['num_plate'] == plate]

    graphs = []

    for _, row in matching_rows.iterrows():
        route = row['route'].strip("[]").split(", ")
        times = row['times'].strip("[]").split(", ")
        nodes = set(route)
        links = [{"source": route[i], "target": route[i+1], "time": float(times[i])} for i in range(len(route) - 1)]
        graphs.append({"nodes": [{"id": node} for node in nodes], "links": links})

    with open(json_output_path, 'w') as f:
        json.dump(graphs, f, indent=4)


def generate_insertions(route):
    insertions = {}

    for i, start_node in enumerate(route):
        for j, end_node in enumerate(route):
            if i < j:
                intermediate_nodes = route[i + 1:j]
                if intermediate_nodes:
                    insertions[(start_node, end_node)] = intermediate_nodes
            elif i > j:
                intermediate_nodes = route[i - 1:j:-1]
                if intermediate_nodes:
                    insertions[(start_node, end_node)] = intermediate_nodes

    return insertions
