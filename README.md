# LPR Data Processing and Visualization Software

## Overview
"LPR Data Processing and Visualization Software" is a desktop application designed for processing, correcting, and visualizing vehicle license plate data captured through a License Plate Recognition (LPR) system. This tool allows users to load plate data, apply correction algorithms to enhance data accuracy, calculate routes based on the corrected plates, and visualize these routes through graphs.

## Features
- Load vehicle plate data from CSV files.
- Automatic plate correction using Levenshtein or Damerau-Levenshtein distance algorithms.
- Route calculation and route adjustments based on times between trips.
- Visualization of routes.
- User friendly graphical interface for software interaction.

## Prerequisites
Before installing and running the software, ensure you have Python 3.6 or higher installed, as well as the following packages:
- pandas
- tkinter
- PIL (Python Imaging Library)
- plotly
- networkx

## Installation
To install the software and all necessary dependencies, follow these steps:

1. Clone the repository to your local machine:
git clone https://github.com/SmartPoqueira/PathCleaner

2. Navigate to the project directory:
cd PathCleaner

3. Install the dependencies using `pip`:
pip install -r requirements.txt


## Usage
To start the application, run the following command in the project directory:
python main.py

Follow the instructions in the graphical interface to load data, select correction algorithms, and view the results.

## Contributing
If you have a suggestion that would make this better, please fork the repository and create a pull request.

## Contact
Your Name - albduranlopez@ugr.es

Project Link: https://wpd.ugr.es/~smartpoqueira/en/

