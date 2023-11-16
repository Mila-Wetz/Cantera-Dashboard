#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 15 21:49:19 2023

@author: sachinnnair
"""

#pip install pandas


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Replace 'file_path.xlsx' with the path to your Excel file
file_path = 'ExampleOutputData.xlsx'

# Read the Excel file
excel_data = pd.read_excel(file_path)

# Store each column as a list
data = {}
for column in excel_data.columns:
    data[column] = excel_data[column].tolist()

# Access the lists by column name
# For example, to access the list of values in the 'Column_name' column:
# column_list = columns_as_lists['Column_name']

c_angle = data['CAD']
vol = data['Vol']
press = data['Pressure']


#plt.switch_backend('Qt5Agg')
#plt.switch_backend('TkAgg')

root = tk.Tk()
root.title("Plots")


# # Create a Matplotlib figure and subplot
# fig, ax = plt.subplots()
# ax.plot(c_angle,press)


fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)


# Plot data on the first subplot
ax1.plot(c_angle,press)
ax1.set_title('Plot 1')  # Set title for the first plot

# Plot data on the second subplot
ax2.plot(vol,press)
ax2.set_title('Plot 2')  # Set title for the second plot


# Create a canvas to display Matplotlib plots in the Tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()

plt.close(fig)

# Add the Matplotlib canvas to the Tkinter window
canvas.get_tk_widget().pack()

# Run the Tkinter main loop
root.mainloop()










