import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from PIL import Image, ImageTk
import pandas as pd

from correctors import LevenshteinCorrector, DamerauLevenshteinCorrector
from route_calculators import SimpleRouteCalculator
from data_processor import DataProcessor
from data_gui_processing import generate_insertions, convert_plate_to_graphs_json
from plotting import generate_and_save_plotly_graph


class ProfessionalTkinterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LPR Data Processing and Visualization Software")
        self.geometry("1000x600")
        self.configure(bg='white')

        self.processed_file_path = None
        self.distance_algorithm = tk.StringVar(value="levenshtein")

        self.style = ttk.Style(self)
        self.style.configure('TButton', font=('Helvetica', 12), borderwidth='4')
        self.style.configure('TLabel', font=('Helvetica', 14), background='white')
        self.style.map('TButton', foreground=[('active', '!disabled', 'blue')],
                       background=[('active', 'black')])


        self.normalize_data = tk.BooleanVar(value=False)
        self.create_notebook()
        self.create_widgets()
        self.create_treeview()



    def create_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        self.controls_frame = ttk.Frame(self.notebook)
        self.graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.controls_frame, text='Controls')
        self.notebook.add(self.graph_frame, text='Graph')


    def create_widgets(self):
        self.top_frame = tk.Frame(self.controls_frame)
        self.top_frame.pack(fill='x')
        self.title_label = ttk.Label(self.top_frame, text="LPR Data Processing & Visualization", font=('Helvetica', 18, 'bold'))
        self.title_label.pack()
        self.description_label = ttk.Label(self.top_frame, text="Convert, Correct Plates, Calculate Routes, and Visualize Graphs", font=('Helvetica', 14))
        self.description_label.pack()
        self.main_frame = tk.Frame(self.controls_frame)
        self.main_frame.pack(fill='both', expand=True, padx=50)

        button_width = 200
        button_padx = (50, 50)

        self.load_button_frame = tk.Frame(self.main_frame)
        self.load_button_frame.pack(pady=5, fill='x', expand=True)
        self.load_button = ttk.Button(self.load_button_frame, text="Select Data File", command=self.load_file, width=button_width)
        self.load_button.pack(side='left', padx=button_padx)


        self.algorithm_route_frame = tk.Frame(self.main_frame)
        self.algorithm_route_frame.pack(pady=10, fill='x', expand=True)

        self.distance_algorithm_frame = tk.Frame(self.algorithm_route_frame, width=button_width)
        self.distance_algorithm_frame.pack(side='left', padx=button_padx)
        ttk.Label(self.distance_algorithm_frame, text="Select Distance Algorithm:", anchor='center').pack(fill='x')
        levenshtein_radio = ttk.Radiobutton(self.distance_algorithm_frame, text="Levenshtein", variable=self.distance_algorithm, value="levenshtein")
        damerau_radio = ttk.Radiobutton(self.distance_algorithm_frame, text="Damerau-Levenshtein", variable=self.distance_algorithm, value="damerau")
        levenshtein_radio.pack(anchor='w', pady=2)
        damerau_radio.pack(anchor='w', pady=2)

        self.normalize_checkbutton = ttk.Checkbutton(self.distance_algorithm_frame, text="Normalize Plates", variable=self.normalize_data)
        self.normalize_checkbutton.pack(anchor='w', pady=2)

        self.max_time_between_frame = tk.Frame(self.main_frame)
        self.max_time_between_frame.pack(pady=10, fill='x', expand=True)
        self.max_time_between_label = ttk.Label(self.max_time_between_frame, text="Max Time Between Trips (minutes):", anchor='w')
        self.max_time_between_label.pack(side='left', padx=(50, 10))
        self.max_time_between_input = ttk.Entry(self.max_time_between_frame, width=20)
        self.max_time_between_input.pack(side='left', fill='x', padx=(0, 10))
        self.max_time_between_input.insert(0, "1440")

        self.route_input_frame = tk.Frame(self.algorithm_route_frame, width=button_width)
        self.route_input_frame.pack(side='right', padx=button_padx)
        ttk.Label(self.route_input_frame, text="Enter Route (comma separated):", anchor='center').pack(fill='x')
        self.route_input = ttk.Entry(self.route_input_frame)
        self.route_input.pack(fill='x', pady=2)

        self.process_button_frame = tk.Frame(self.main_frame)
        self.process_button_frame.pack(pady=5, fill='x', expand=True)
        self.process_button = ttk.Button(self.process_button_frame, text="Process Data", state='disabled', command=self.start_processing, width=button_width)
        self.process_button.pack(side='left', padx=button_padx)

        self.save_button_frame = tk.Frame(self.main_frame)
        self.save_button_frame.pack(pady=5, fill='x', expand=True)
        self.save_button = ttk.Button(self.save_button_frame, text="Save Processed Data", state='disabled', command=self.save_data, width=button_width)
        self.save_button.pack(side='left', padx=button_padx)

        self.status_label = ttk.Label(self.main_frame, text="Status: Waiting for file...", font=('Helvetica', 12))
        self.status_label.pack(pady=20)
        self.csv_note_label = ttk.Label(self.main_frame, text="Note: Only .csv files", font=('Helvetica', 10))
        self.csv_note_label.pack(pady=(0, 10))
        self.selected_file_label = ttk.Label(self.main_frame, text="", font=('Helvetica', 10))
        self.selected_file_label.pack(pady=(0, 20))

        self.close_button = ttk.Button(self, text="Close", command=self.close_app)
        self.close_button.place(relx=1.0, rely=1.0, anchor='se')


    def create_treeview(self):
        self.graph_tab_frame = ttk.Frame(self.graph_frame)
        self.graph_tab_frame.pack(fill='both', expand=True)

        self.tree_frame = ttk.Frame(self.graph_tab_frame)
        self.tree_frame.pack(side="left", fill="y", expand=False)

        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(side="left", fill="y")

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.tree.bind('<<TreeviewSelect>>', self.on_item_selected)

        self.graph_display_frame = ttk.Frame(self.graph_tab_frame)
        self.graph_display_frame.pack(side="right", fill="both", expand=True)

    def display_graph_image(self, image_path):
        if hasattr(self, 'graph_image_label'):
            self.graph_image_label.destroy()

        graph_image = Image.open(image_path)
        graph_image = graph_image.resize((800, 600), Image.Resampling.LANCZOS)
        graph_photo = ImageTk.PhotoImage(graph_image)

        self.graph_image_label = tk.Label(self.graph_display_frame, image=graph_photo)
        self.graph_image_label.image = graph_photo
        self.graph_image_label.pack(fill="both", expand=True)

    def on_item_selected(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            item = self.tree.item(selected_items[0])
            plate = item['values'][0]
            if self.processed_file_path:
                convert_plate_to_graphs_json(self.processed_file_path, plate, 'graphs_data.json')
                generate_and_save_plotly_graph('graphs_data.json', 'graph.png')
                self.display_graph_image('graph.png')
            else:
                messagebox.showwarning("Warning", "No processed data file available. Please process and save data first.")

    def load_data_into_treeview(self, filepath):
        for i in self.tree.get_children():
            self.tree.delete(i)

        data = pd.read_csv(filepath)

        self.tree["columns"] = list(data.columns)
        self.tree["show"] = "headings"

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        for _, row in data.iterrows():
            self.tree.insert("", "end", values=list(row))


    def close_app(self):
        self.destroy()


    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            self.filepath = filepath
            self.selected_file_label.config(text=f"Selected File: {filepath.split('/')[-1]}")
            self.status_label.config(text="Status: File loaded")
            self.process_button['state'] = 'normal'


    def start_processing(self):
        self.status_label.config(text="Status: Processing data...")
        self.process_button['state'] = 'disabled'
        self.load_button['state'] = 'disabled'

        if self.distance_algorithm.get() == "levenshtein":
            corrector = LevenshteinCorrector(normalize=self.normalize_data.get())
        elif self.distance_algorithm.get() == "damerau":
            corrector = DamerauLevenshteinCorrector(normalize=self.normalize_data.get())
        else:
            corrector = None

        user_route_str = self.route_input.get()
        user_route_list = user_route_str.split(',')
        user_route_list = [node.strip() for node in user_route_list]
        self.insertions = generate_insertions(user_route_list)
        self.max_time_between_trips = int(self.max_time_between_input.get())
        thread = threading.Thread(target=self.process_data)
        thread.start()


    def process_data(self):
        try:
            self.status_label.config(text="Status: Loading and preparing data...")
            self.update()

            if self.distance_algorithm.get() == "levenshtein":
                corrector = LevenshteinCorrector()
            elif self.distance_algorithm.get() == "damerau":
                corrector = DamerauLevenshteinCorrector()
            else:
                corrector = None

            route_calculator = SimpleRouteCalculator()
            self.processor = DataProcessor(self.filepath, corrector, route_calculator)

            self.processor.load_and_prepare_data()
            self.status_label.config(text="Status: Correcting number plates...")
            self.update()

            self.processor.correct_num_plates_and_remove_hashes()

            self.status_label.config(text="Status: Calculating and adjusting routes...")
            self.update()

            self.processor.calculate_and_adjust_routes(self.max_time_between_trips, self.insertions)
            self.processor.verify_and_classify_visits()

            self.after(100, lambda: self.status_label.config(text="Status: Data processed"))
            self.after(100, self.enable_save_button)
        finally:
            self.after(100, self.enable_load_button)

    def enable_save_button(self):
        self.save_button['state'] = 'normal'

    def enable_load_button(self):
        self.load_button['state'] = 'normal'


    def save_data(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if save_path:
            self.processor.data.to_csv(save_path, index=False)
            self.processed_file_path = save_path
            self.status_label.config(text="Status: Data saved successfully")
            messagebox.showinfo("Save Successful", "The processed data has been saved successfully.")
            self.load_data_into_treeview(save_path)
