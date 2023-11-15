import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def update_sine_wave():
    amplitude = amplitude_slider.get()
    frequency = frequency_slider.get()
    x = np.linspace(0, 2 * np.pi, 100)
    y = amplitude * np.sin(frequency * x)
    sine_wave_plot.clear()
    sine_wave_plot.plot(x, y)
    sine_wave_plot.set_title(f"Sine Wave: Amplitude={amplitude}, Frequency={frequency}")
    sine_wave_canvas.draw()
    root.after(100, update_sine_wave)  # Update every 100ms

root = tk.Tk()
root.title("Real-Time Sine Wave Simulation")

amplitude_slider = tk.Scale(root, label="Amplitude", from_=1, to=10, orient="horizontal")
amplitude_slider.pack()
frequency_slider = tk.Scale(root, label="Frequency", from_=1, to=10, orient="horizontal")
frequency_slider.pack()

fig = Figure(figsize=(5, 4), dpi=100)
sine_wave_plot = fig.add_subplot(111)
sine_wave_canvas = FigureCanvasTkAgg(fig, master=root)
sine_wave_canvas.get_tk_widget().pack()

update_sine_wave()

root.mainloop()

#######################################################################################################################
#######################################################################################################################

import tkinter as tk
import random

# Particle class representing a moving particle
class Particle:
    def __init__(self, canvas, color, radius, x, y, velocity_x, velocity_y):
        self.canvas = canvas
        self.radius = radius
        self.id = canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill=color
        )
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y

    def move(self):
        self.canvas.move(self.id, self.velocity_x, self.velocity_y)
        pos = self.canvas.coords(self.id)
        if pos[0] <= 0 or pos[2] >= canvas_width:
            self.velocity_x *= -1
        if pos[1] <= 0 or pos[3] >= canvas_height:
            self.velocity_y *= -1

# Function to update the particle positions
def update_particles():
    for particle in particles:
        particle.move()
    root.after(20, update_particles)

# Create the main window
root = tk.Tk()
root.title("Particle Collision Simulation")

# Create a canvas for the particles
canvas_width = 400
canvas_height = 400
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height)
canvas.pack()

# Create two particles with random initial positions and velocities
particles = [
    Particle(canvas, "red", 20, random.randint(50, 350), random.randint(50, 350), random.randint(2, 5), random.randint(2, 5)),
    Particle(canvas, "blue", 20, random.randint(50, 350), random.randint(50, 350), random.randint(2, 5), random.randint(2, 5))
]

# Start the particle update loop
update_particles()

root.mainloop()

#######################################################################################################################
#######################################################################################################################

import tkinter as tk
import threading
import random
import time

# Global variables
running = False

def simulate_data():
    while running:

        x = np.linspace(0, 2 * np.pi, 100)
        y = amplitude * np.sin(frequency * x)
        sine_wave_plot.clear()
        sine_wave_plot.plot(x, y)
        sine_wave_plot.set_title(f"Sine Wave: Amplitude={amplitude}, Frequency={frequency}")
        sine_wave_canvas.draw()
        root.after(100, update_sine_wave)  # Update every 100ms

def start_simulation():
    global running
    running = True
    t = threading.Thread(target=simulate_data)
    t.start()

def stop_simulation():
    global running
    running = False


amplitude_slider = tk.Scale(root, label="Amplitude", from_=1, to=10, orient="horizontal")
amplitude_slider.pack()
frequency_slider = tk.Scale(root, label="Frequency", from_=1, to=10, orient="horizontal")
frequency_slider.pack()


# Create the GUI
root = tk.Tk()
root.title("Continuous Simulation with Start and Stop")

fig = Figure(figsize=(5, 4), dpi=100)
sine_wave_plot = fig.add_subplot(111)
sine_wave_canvas = FigureCanvasTkAgg(fig, master=root)
sine_wave_canvas.get_tk_widget().pack()

start_button = tk.Button(root, text="Start Simulation", command=start_simulation)
start_button.pack()

stop_button = tk.Button(root, text="Stop Simulation", command=stop_simulation)
stop_button.pack()

# Create a canvas for plotting

root.mainloop()
