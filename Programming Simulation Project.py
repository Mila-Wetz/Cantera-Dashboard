import tkinter as tk
from tkinter import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math
from tkinter.font import Font
import time
import cantera as ct

#########################################################################
# Input Parameters
#########################################################################

# reaction mechanism, kinetics type and compositions
reaction_mechanism = 'nDodecane_Reitz.yaml'
phase_name = 'nDodecane_IG'
comp_air = 'o2:1, n2:3.76'
comp_fuel = 'c12h26:1'

Engine_Speed = 3000. / 60.  # engine speed [1/s] (3000 rpm)
V_H = .5e-3  # displaced volume [m**3]
epsilon = 20.  # compression ratio [-]
d_piston = 0.083  # piston diameter [m]

# turbocharger temperature, pressure, and composition
T_inlet = 300.  # K
p_inlet = 1.3e5  # Pa
comp_inlet = comp_air

# outlet pressure
p_outlet = 1.2e5  # Pa

# fuel properties (gaseous!)
T_injector = 300.  # K
p_injector = 1600e5  # Pa
comp_injector = comp_fuel

# ambient properties
T_ambient = 300.  # K
p_ambient = 1e5  # Pa
comp_ambient = comp_air

# Inlet valve friction coefficient, open and close timings
inlet_valve_coeff = 1.e-6
inlet_open = -18. / 180. * np.pi
inlet_close = 198. / 180. * np.pi

# Outlet valve friction coefficient, open and close timings
outlet_valve_coeff = 1.e-6
outlet_open = 522. / 180 * np.pi
outlet_close = 18. / 180. * np.pi

# Simulation time and parameters
sim_n_revolutions = 2
delta_T_max = 20.
rtol = 1.e-12
atol = 1.e-16

# Additional IC Parameters
V_oT = V_H / (epsilon - 1.)
A_piston = .25 * np.pi * d_piston ** 2
stroke = V_H / A_piston


def crank_angle(t):
    """Convert time to crank angle"""
    return np.remainder(2 * np.pi * Engine_Speed * t, 4 * np.pi)


def piston_speed(t):
    """Approximate piston speed with sinusoidal velocity profile"""
    return - stroke / 2 * 2 * np.pi * Engine_Speed * np.sin(crank_angle(t))


def ca_ticks(t):
    """Helper function converts time to rounded crank angle."""
    return np.round(crank_angle(t) * 180 / np.pi, decimals=1)


def simulation(throttle):

    # load reaction mechanism and begin constructing reactor network
    gas = ct.Solution(reaction_mechanism, phase_name)

    # define initial state and set up reactor
    gas.TPX = T_inlet, p_inlet, comp_inlet
    cyl = ct.IdealGasReactor(gas)
    cyl.volume = V_oT

    # define inlet state
    gas.TPX = T_inlet, p_inlet, comp_inlet
    inlet = ct.Reservoir(gas)

    # inlet valve
    inlet_valve = ct.Valve(inlet, cyl)
    inlet_delta = np.mod(inlet_close - inlet_open, 4 * np.pi)
    inlet_valve.valve_coeff = inlet_valve_coeff
    inlet_valve.set_time_function(
        lambda t: np.mod(crank_angle(t) - inlet_open, 4 * np.pi) < inlet_delta)

    # define injector state (gaseous!)
    gas.TPX = T_injector, p_injector, comp_injector
    injector = ct.Reservoir(gas)

    # define outlet pressure (temperature and composition don't matter)
    gas.TPX = T_ambient, p_outlet, comp_ambient
    outlet = ct.Reservoir(gas)

    # outlet valve
    outlet_valve = ct.Valve(cyl, outlet)
    outlet_delta = np.mod(outlet_close - outlet_open, 4 * np.pi)
    outlet_valve.valve_coeff = outlet_valve_coeff
    outlet_valve.set_time_function(
        lambda t: np.mod(crank_angle(t) - outlet_open, 4 * np.pi) < outlet_delta)

    # define ambient pressure (temperature and composition don't matter)
    gas.TPX = T_ambient, p_ambient, comp_ambient
    ambient_air = ct.Reservoir(gas)

    # piston is modeled as a moving wall
    piston = ct.Wall(ambient_air, cyl)
    piston.area = A_piston
    piston.set_velocity(piston_speed)

    # create a reactor network containing the cylinder and limit advance step
    sim = ct.ReactorNet([cyl])
    sim.rtol, sim.atol = rtol, atol
    cyl.set_advance_limit('temperature', delta_T_max)

    # Fuel mass, injector open and close timings
    injector_open = 350. / 180. * np.pi
    injector_close = 365. / 180. * np.pi
    injector_mass = 3.2e-5 * throttle * 1.5  # kg

    # injector is modeled as a mass flow controller
    injector_mfc = ct.MassFlowController(injector, cyl)
    injector_delta = np.mod(injector_close - injector_open, 4 * np.pi)
    injector_t_open = (injector_close - injector_open) / 2. / np.pi / Engine_Speed
    injector_mfc.mass_flow_coeff = injector_mass / injector_t_open
    injector_mfc.set_time_function(
        lambda t: np.mod(crank_angle(t) - injector_open, 4 * np.pi) < injector_delta)

    # initialize output array
    states = ct.SolutionArray(cyl.thermo, extra=('t', 'ca', 'V', 'm', 'mdot_in', 'mdot_out',
                                                 'dWv_dt'), )

    # Simulate with a maximum resolution of 2 deg crank angle
    dt = 2 / (360 * Engine_Speed)
    t_stop = sim_n_revolutions / Engine_Speed

    # Perform simulation
    while sim.time < t_stop:
        # perform time integration
        sim.advance(sim.time + dt)

        # calculate results to be stored
        dWv_dt = - (cyl.thermo.P - ambient_air.thermo.P) * A_piston * \
                 piston_speed(sim.time)

        # append output data
        states.append(cyl.thermo.state,
                      t=sim.time, ca=crank_angle(sim.time),
                      V=cyl.volume, m=cyl.mass,
                      mdot_in=inlet_valve.mass_flow_rate,
                      mdot_out=outlet_valve.mass_flow_rate,
                      dWv_dt=dWv_dt)

    return states


def update_simulation():
    gearshift = gearshift_slider.get()
    throttle = throttle_slider.get()
    states = simulation(throttle)
    sine_wave_plots[0].clear()  # Clear first subplot
    sine_wave_plots[0].plot(states.ca, states.P)  # Plot on first subplot
    sine_wave_plots[0].set_title('P vs crank angle')

    sine_wave_plots[1].clear()  # Clear second subplot
    sine_wave_plots[1].plot(states.V, states.P)  # Plot on second subplot
    sine_wave_plots[1].set_title('P vs V')
    sine_wave_canvas.draw()
    root.after(100, update_simulation)  # Update every 100ms


width, height = 400, 400  # Dimensions of the canvas.
len1, len2 = 0.85, 0.3  # Dimensions of the needle, relative to the canvas ray.
ray = int(0.7 * width / 2)  # Radius of the dial.
x0, y0 = width / 2, width / 2  # Position of the center of the circle.
min_speed, max_speed = 0, 220  # Max and min values on the dial. Adjust according to need.
step_speed = 20  # Least count or smallest division on the dial which has a text value displayed.
min_rpm, max_rpm = 0, 8  # Max and min values on the dial. Adjust according to need.
step_rpm = 1  # Least count or smallest division on the dial which has a text value displayed. Adjust according to need.

root = tk.Tk()
root.title("Real-Time Sine Wave Simulation")
meter_font = Font(family="Tahoma", size=12, weight='normal')  # The font used in the meter. Feel free to play around.
temp = [5, 7, 9, 2, 3]

gearshift_slider = tk.Scale(root, label="Gearshift", from_=1, to=10, orient="vertical")
gearshift_slider.pack(side=tk.LEFT)
throttle_slider = tk.Scale(root, label="Throttle", from_=1, to=10, orient="vertical")
throttle_slider.pack(side=tk.LEFT)

fig = Figure(figsize=(8, 4), dpi=100)
sine_wave_plots = [fig.add_subplot(1, 2, i + 1) for i in range(2)]  # Create two subplots
sine_wave_canvas = FigureCanvasTkAgg(fig, master=root)
sine_wave_canvas.get_tk_widget().pack()


def setTitles():
    root.title('Speedometer')
    speed.itemconfig(speed.title, text='Speed')
    speed.itemconfig(speed.unit, text='KMPH')
    rpm.itemconfig(rpm.title, text='RPM')
    rpm.itemconfig(rpm.unit, text='x1000')


class Meter(Canvas):

    def draw(self, vmin, vmax, step, title, unit):
        self.vmin = vmin
        self.vmax = vmax
        x0 = width / 2
        y0 = width / 2
        ray = int(0.7 * width / 2)
        self.title = self.create_text(width / 2, 12, fill="#000",
                                      font=meter_font)  # Window title.
        self.create_oval(x0 - ray * 1.1, y0 - ray * 1.1, x0 + ray * 1.1, y0 + ray * 1.1,
                         fill="blue")  # The gray outer ring.
        self.create_oval(x0 - ray, y0 - ray, x0 + ray, y0 + ray, fill="#000")  # The dial.
        coef = 0.1
        self.create_oval(x0 - ray * coef, y0 - ray * coef, x0 + ray * coef, y0 + ray * coef,
                         fill="white")  # This is the connection point blob of the needle.

        # This loop fills in the values at each step or gradation of the dial.
        for i in range(1 + int((vmax - vmin) / step)):
            v = vmin + step * i
            angle = (5 + 6 * ((v - vmin) / (vmax - vmin))) * math.pi / 4
            self.create_line(x0 + ray * math.sin(angle) * 0.9,
                             y0 - ray * math.cos(angle) * 0.9,
                             x0 + ray * math.sin(angle) * 0.98,
                             y0 - ray * math.cos(angle) * 0.98, fill="#FFF", width=2)
            self.create_text(x0 + ray * math.sin(angle) * 0.75,
                             y0 - ray * math.cos(angle) * 0.75,
                             text=v, fill="#FFF", font=meter_font)
            if i == int(vmax - vmin) / step:
                continue
            for dv in range(1, 5):
                angle = (5 + 6 * ((v + dv * (step / 5) - vmin) / (vmax - vmin))) * math.pi / 4
                self.create_line(x0 + ray * math.sin(angle) * 0.94,
                                 y0 - ray * math.cos(angle) * 0.94,
                                 x0 + ray * math.sin(angle) * 0.98,
                                 y0 - ray * math.cos(angle) * 0.98, fill="#FFF")
        self.unit = self.create_text(width / 2, y0 + 0.8 * ray, fill="#FFF",
                                     font=meter_font)
        self.needle = self.create_line(x0 - ray * math.sin(5 * math.pi / 4) * len2,
                                       y0 + ray * math.cos(5 * math.pi / 4) * len2,
                                       x0 + ray * math.sin(5 * math.pi / 4) * len1,
                                       y0 - ray * math.cos(5 * math.pi / 4) * len1,
                                       width=2, fill="#FFF")
        lb1 = Label(self, compound='right', textvariable=v)

    # Draws the needle based on the speed or input value.
    def draw_needle(self, v):
        print(v)  # Not required, but helps in debugging.
        v = max(v, self.vmin)  # If input is less than 0 then the pointer stays at 0
        v = min(v,
                self.vmax)  # If input is greater than the greatest value then the pointer stays at the maximum value.
        angle = (5 + 6 * ((v - self.vmin) / (self.vmax - self.vmin))) * math.pi / 4
        self.coords(self.needle, x0 - ray * math.sin(angle) * len2,
                    y0 + ray * math.cos(angle) * len2,
                    x0 + ray * math.sin(angle) * len1,
                    y0 - ray * math.cos(angle) * len1)


meters = Frame(root, width=width, height=width, bg="white")
speed = Meter(meters, width=width, height=height)
speed.draw(min_speed, max_speed, step_speed, "Speed", "KMPH")
speed.pack(side=LEFT)
meters.pack(side=LEFT, anchor=SE, fill=Y, expand=True)
meters = Frame(root, width=width, height=width, bg="white")
rpm = Meter(meters, width=width, height=height)
rpm.draw(min_rpm, max_rpm, step_rpm, "RPM", "x1000")
rpm.pack(side=RIGHT)
meters.pack(anchor=SE, fill=Y, expand=True)
setTitles()

# Digital value zone.
cSpeed = Canvas(root, width=30, height=30, bg="white")
cSpeed.place(x=width * 0.5, y=0.6 * height)
x = Message(cSpeed, width=100, text='')
x.place(x=0, y=0)
x.pack()
cRpm = Canvas(root, width=30, height=30, bg="white")
cRpm.place(x=1.5 * width, y=0.6 * height)
y = Message(cRpm, width=100, text='')
y.place(x=0, y=0)
y.pack()


def meter_update():  # funtion that updates the gauges
    # Calculate engine speed based on throttle position and gear shift
    Speed_throttle = throttle_slider.get()
    Speed_Gearshift = gearshift_slider.get()
    kmph = Engine_Speed * Speed_throttle * (11/12) / 5
    rev = Engine_Speed * Speed_Gearshift / 10
    speed.draw_needle(kmph)
    rpm.draw_needle(rev)
    x.config(text=kmph)
    y.config(text=rev)
    root.after(500, meter_update)


while True:
    meter_update()
    update_simulation()
    root.update_idletasks()
    root.update()
    root.mainloop()
    time.sleep(1)



