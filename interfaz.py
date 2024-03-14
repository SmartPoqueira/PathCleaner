import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from PIL import Image, ImageTk
from herencia_software import *
import plotly.graph_objects as go
import plotly.io as pio
import json
import networkx as nx
import pandas as pd


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


def generate_and_save_plotly_graph(json_output_path, image_output_path):
    with open(json_output_path) as f:
        graphs = json.load(f)

    graph_data = graphs[0]
    G = nx.Graph()
    for node in graph_data['nodes']:
        G.add_node(node['id'])

    for link in graph_data['links']:
        G.add_edge(link['source'], link['target'], weight=link['time'])

    pos = nx.spring_layout(G, k=0.5, iterations=50)

    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])

    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=10,
            color=[],
            line=dict(width=2)
        )
    )
    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['text'] += tuple([node])

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>Network graph made with Python',
                        titlefont=dict(size=16),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="Python code: <a href='https://www.python.org/'> https://www.python.org/</a>",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 ) ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.write_image(image_output_path)
