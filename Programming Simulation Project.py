import tkinter as tk
from tkinter import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math
from tkinter.font import Font
import cantera as ct
from scipy.integrate import trapz


def simulation(throttle, turbo, injection_time, AFR_adjustment, Gearshift, Compression_Ratio):

    def crank_angle(t):
        """Convert time to crank angle"""
        return np.remainder(2 * np.pi * Engine_Speed * t, 4 * np.pi)

    def piston_speed(t):
        """Approximate piston speed with sinusoidal velocity profile"""
        return - stroke / 2 * 2 * np.pi * Engine_Speed * np.sin(crank_angle(t))

    # IC Parameters
    d_piston = 0.083   # piston diameter [m]
    epsilon = Compression_Ratio  # compression ratio [-]
    V_H = .5e-3  # displaced volume [m**3]
    V_oT = V_H / (epsilon - 1.)
    A_piston = .25 * np.pi * d_piston ** 2
    stroke = V_H / A_piston

    # reaction mechanism, kinetics type and compositions
    reaction_mechanism = 'nDodecane_Reitz.yaml'
    phase_name = 'nDodecane_IG'
    comp_air = 'o2:1, n2:3.76'
    comp_fuel = 'c12h26:1'

    # Simulation time and parameters
    Engine_Speed = (1000. / 60.) * Gearshift  # engine speed [1/s] (3000 rpm)
    sim_n_revolutions = 2
    delta_T_max = 20.
    rtol = 1.e-12
    atol = 1.e-16

    # turbocharger temperature, pressure, and composition
    T_inlet = 300  # K
    p_inlet = 1.3e5 + (turbo * 1000)  # Pa
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
    inlet_valve_coeff = 2.75e-7 + (AFR_adjustment * 3.5e-6)
    inlet_open = -18. / 180. * np.pi
    inlet_close = 198. / 180. * np.pi

    # Outlet valve friction coefficient, open and close timings
    outlet_valve_coeff = 1.e-6
    outlet_open = 522. / 180 * np.pi
    outlet_close = 18. / 180. * np.pi

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
    injector_open = (350 - injection_time) / 180. * np.pi
    injector_close = (365 - injection_time) / 180. * np.pi
    injector_mass = 1.5e-5 + (throttle * .1 * 1.5e-5)  # kg

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
    dt = 1 / (360 * Engine_Speed)
    t_stop = sim_n_revolutions / Engine_Speed

    # Perform simulation
    while sim.time < t_stop:
        # perform time integration
        sim.advance(sim.time + dt)

        # calculate results to be stored
        dWv_dt = - (cyl.thermo.P - ambient_air.thermo.P) * A_piston * piston_speed(sim.time)

        # append output data
        states.append(cyl.thermo.state,
                      t=sim.time, ca=crank_angle(sim.time),
                      V=cyl.volume, m=cyl.mass,
                      mdot_in=inlet_valve.mass_flow_rate,
                      mdot_out=outlet_valve.mass_flow_rate,
                      dWv_dt=dWv_dt)

    # heat release to be plotted and output to GUI
    Q_text = trapz(states.heat_release_rate * states.V, states.t)
    Q_textbox.delete(1.0, tk.END)  # Clear previous content
    Q_textbox.insert(tk.END, "{:.2f}".format(Q_text))

    # expansion power to be output to GUI
    power_text = trapz(states.dWv_dt, states.t)
    power_textbox.delete(1.0, tk.END)  # Clear previous content
    power_textbox.insert(tk.END, power_text)

    # efficiency
    efficiency_text = power_text / Q_text
    efficiency_textbox.delete(1.0, tk.END)  # Clear previous content
    efficiency_textbox.insert(tk.END, "{:.2f}".format(efficiency_text * 100))
    # warnings
    if power_text < 100:
        warning_text = "No combustion possible, increase fuel injection with throttle or air intake properties"
    else:
        warning_text = "No warnings. Engine is running"
    error_textbox.delete(1.0, tk.END)
    error_textbox.insert(tk.END, warning_text)

    # AFR to be output to GUI
    total_mdot_in = trapz(states.mdot_in, states.t)
    AFR_text = total_mdot_in / injector_mass
    AFR_textbox.delete(1.0, tk.END)  # Clear previous content
    AFR_textbox.insert(tk.END, "{:.2f}".format(AFR_text))

    return states


def update_simulation():
    def crank_angle(t):
        """Convert time to crank angle"""
        return np.remainder(2 * np.pi * Engine_Speed * t, 4 * np.pi)

    # Assign values from GUI to perform simulation
    throttle = throttle_slider.get()
    injection_time = injection_time_slider.get()
    turbo = turbo_slider.get()
    AFR_adjustment = AFR_slider.get()
    Gearshift = gearshift_slider.get()
    Engine_Speed = (1000. / 60.) * Gearshift  # engine speed [1/s]
    Compression_Ratio = Compression_Ratio_Slider.get()
    states = simulation(throttle, turbo, injection_time, AFR_adjustment, Gearshift, Compression_Ratio)

    # plot crank angle vs pressure
    simulation_plots[0].clear()  # Clear first subplot
    simulation_plots[0].set_title('Cylinder Pressure vs Crank Angle Degree')
    simulation_plots[0].set_xlabel(r'$\phi$ [deg]')
    simulation_plots[0].set_ylabel('Cylinder Pressure (kPa)')
    simulation_plots[0].set_ylim(0, 25000)
    simulation_plots[0].plot(crank_angle(states.t) * 57.6, states.P / 1000)
    simulation_plots[0].grid()

    # plot volume vs pressure
    simulation_plots[1].clear()  # Clear second subplot
    simulation_plots[1].set_title('Cylinder Pressure vs Volume')
    simulation_plots[1].set_xlabel(r'Volume ($\times 10^{-4}$ L)')
    simulation_plots[1].set_ylim(0, 25000)
    simulation_plots[1].plot(states.V * 10000, states.P / 1000)
    simulation_plots[1].grid()
    simulation_canvas.draw()
    root.after(100, update_simulation)  # Update every 100ms


#######################################################################################################################
#                                                                                                                     #
# Edit the GUI window size by decreasing or increasing the width and height in the following line                     #
#######################################################################################################################
width, height = 400, 400  # Dimensions of the canvas.

# Define properties for gauges
len1, len2 = 0.85, 0.3  # Dimensions of the needle, relative to the canvas ray.
ray = int(0.7 * width / 2)  # Radius of the dial.
x0, y0 = width / 2, width / 2  # Position of the center of the circle.
min_speed, max_speed = 0, 220  # Max and min values on the dial.
step_speed = 20  # Least count or smallest division on the dial which has a text value displayed.
min_rpm, max_rpm = 0, 8  # Max and min values on the dial.
step_rpm = 1  # Least count or smallest division on the dial which has a text value displayed.

root = tk.Tk()
root.title("Real-Time Diesel Engine Simulation")
meter_font = Font(family="Tahoma", size=12, weight='normal')

# Create engine speed slider
gearshift_slider = tk.Scale(root, label="Gearshift", from_=1, to=8, orient="vertical")
gearshift_slider.grid(row=7, column=1, rowspan=2)

# Create throttle slider
throttle_slider = tk.Scale(root, label="Throttle", from_=1, to=10, orient="vertical")
throttle_slider.grid(row=5, column=1, rowspan=2)

# Create turbo slider
turbo_slider = tk.Scale(root, label="Turbo Boost Pressure", from_=1, to=10, orient="vertical")
turbo_slider.grid(row=5, column=2, rowspan=2)

# Create injection time slider
injection_time_slider = tk.Scale(root, label="Adjust Injection Timing", from_=-5, to=5, orient="vertical")
injection_time_slider.grid(row=5, column=0, rowspan=2)

# Create AFR Slider
AFR_slider = tk.Scale(root, label="Adjust Air to Fuel Ratio", from_=0, to=10, orient="vertical")
AFR_slider.grid(row=7, column=0, rowspan=2)

# Create Compression Ratio Slider
Compression_Ratio_Slider = tk.Scale(root, label="Adjust Engine Compression Ratio", from_=15, to=20, orient="vertical")
Compression_Ratio_Slider.grid(row=7, column=2, rowspan=2)

# Create power textbox for simulation results
power_textbox = tk.Text(root, height=1, width=4)
Label(root, text="Power, kilowatts").grid(row=0, column=0, padx=30)
power_textbox.grid(row=1, column=0, padx=30)

# Create heat release textbox for simulation results
Q_textbox = tk.Text(root, height=1, width=12)
Label(root, text="Adiabatic Heat Release, kJ/cycle").grid(row=0, column=1)
Q_textbox.grid(row=1, column=1)

# Create efficiency textbox for simulation results
efficiency_textbox = tk.Text(root, height=1, width=12)
Label(root, text="Efficiency").grid(row=0, column=2)
efficiency_textbox.grid(row=1, column=2)

# Create AFR textbox for simulation results
AFR_textbox = tk.Text(root, height=1, width=12)
Label(root, text="Air-Fuel Ratio").grid(row=2, column=0)
AFR_textbox.grid(row=3, column=0)

# Warning textbox
error_textbox = tk.Text(root, height=4, width=32)
Label(root, text="Warning").grid(row=2, column=1)
error_textbox.grid(row=3, column=1)

# Create figure object and add plots
fig = Figure(figsize=(8, 4), dpi=100)
simulation_plots = [fig.add_subplot(1, 2, i + 1) for i in range(2)]  # Create two subplots
simulation_canvas = FigureCanvasTkAgg(fig, master=root)
simulation_canvas.get_tk_widget().grid(row=0, column=3, columnspan=4, rowspan=5)


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

    def draw_needle(self, v):
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
speed.grid(row=5, column=3, )
meters.grid(row=6, column=3, rowspan=3)
meters = Frame(root, width=width, height=width, bg="white")
rpm = Meter(meters, width=width, height=height)
rpm.draw(min_rpm, max_rpm, step_rpm, "RPM", "x1000")
rpm.grid(row=5, column=4, )
meters.grid(row=6, column=4, rowspan=3)
setTitles()


def meter_update():  # funtion that updates the gauges
    Speed_throttle = throttle_slider.get()
    kmph = Speed_throttle * 15.5
    rev = gearshift_slider.get()
    speed.draw_needle(kmph)
    rpm.draw_needle(rev)
    root.after(500, meter_update)


meter_update()
update_simulation()
root.update_idletasks()
root.update()
root.mainloop()
