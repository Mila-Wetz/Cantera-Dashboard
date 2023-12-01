
# Cantera-Dashboard
By: Sebastian Riley, Sachin Nair, Mila Wetz

This dashboard is a visual learning tool that runs with the cantera simulation package. This tool allows users to observe how changing various parameters influences the performance of a 4-cylinder internal combustion engine.

The simulation plots and engine performance parameters continuously updates as the slider values are changed based on user inputs. A description of the sliders as they update engine simulation results are found below:

  -Injection timing: The engine timing is the period within the engine cycle that the fuel in injected into the cylinder bore. Typical injection timing for diesel engines ranges from 350 to 365 crank angle degrees with 360 crank angle degrees representing the point in the engine cycle where the piston is at top dead center (AKA the end of the compression stroke). The default setting when the simulation is initially ran sets the injection timing at this interval with slider value set to zero. The injection timing slider ranges from -5 to +5 crank angle degrees. Setting the slider to positive values advances the injection timing while negative values retards the injection timing. Advancing the injection timing allows for the fuel to enter the combustion chamber earlier in the engine cycle which and, in theory, should allow for improved mixing of the air-fuel mixture resulting in more complete combustion. The simulator does a good job at replicating this process as we see peak pressures and engine power increasing when advancing the engine timing.
  
  -Air to fuel ratio: The air to fuel ratio is a unitless engine parameter computed by comparing the amount of air mass to the amount of fuel mass for each engine cycle. The ratio is controlled by the air to fuel ratio slider which ranges from a default value of 0 to a maximum value of 10. The air to fuel ratio slider works by manipulating the air intake valve frictional drag coefficient. The slider has no effect on the mass of the fuel injected each cycle so as not to confuse with the throttle slider functions which will be described next. Increasing the intake valve coeffecient allows for air to enter the combustion chamber each cycle which results in increasing the air to fuel ratio. Proper air to fuel ratios ensure complete combustion, with typical values ranging from 17 to 30, but may be seen to operate at 70+ for specific design conditions. 
  
    -Throttle levels: The throttle slider operates by varying the mass of the fuel injected for each cycle. Increasing the throttler slider values simulates more fuel injected and ranges from 0 to 10. A typical amount of fuel is injected with the slider at its default value of 0 when initially running the simulation. Increasing the slider to its maximum value of 10 doubles the amount of fuel injected. 
    
  -Air Intake Pressure: The air intake pressure simulates running a turbocharger/supercharger on the engine by increasing the pressure and density of the air entering the combustion chamber during the air intake stroke. The slider allows the pressure to range from atmospheric up to ten times that much. The slider default value is atmospheric, and ranges up to a maximum value of 10. Increasing the air pressure results in the density to also increase, allowing for more air to enter the chamber. Note to the user: adjusting this value will also slightly change the values for the air to fuel ratio.
  
  -Gearshift: The gearshift slider attempts to simuate a transmission by adjusting the engine speed at certain operating parameters. The slider ranges from its default value of 1 to a maximum value of 8 which in turn provides engine operating speeds ranging from 1000-8000 rpm at 1000rpm increments. When increasing the engine speed holding all of the other parameters constant, the simulation may result in incomplete combustion. This typically means that combustion is not possible for engine speeds that high. The usual remedy for these scenerios is to increase the throttle, compression ratio, and air to fuel ratio until combustion occurs. 
  
  -Engine compression ratio: The engine compression ratio is an engine design parameter that is computed by dividing the volume of the cylinder bore when the engine is at bottom dead center by the volume of the combustion chamber when the engine is at top dead center. The default value of the slider is 15 and can be increased up to 20 which are typical values for diesel engines. Increasing the compression results in more complete combustion and higher engine performance parameters mainly due to the fact the diesel engine depend on sufficient compression for the fuel to ignite and combustion to occur. 

  
<img src=https://github.com/Mila-Wetz/Cantera-Dashboard/assets/143420424/a6a3bf6e-2c68-487a-ad5b-850ab05ebc54 width ="600" height="350">


The code then uses the user input data from the sliders to simulate the engine with those parameters. It then plots the changes in cylinder pressure vs crank angle and volume and calculates engine performance factors such as:

  -Horsepower
  -Adiabatic Heat Release
  -Efficiency
  -Air-to-Fuel Ratio

<img src=https://github.com/Mila-Wetz/Cantera-Dashboard/assets/143420424/95dd7daf-61f3-497b-9ab1-ab9a86a186cf width="400" height="400">
<img src=https://github.com/Mila-Wetz/Cantera-Dashboard/assets/143420424/f62d9cd1-7fd9-4524-b204-ef9bfc112713 width="500" height="400">

The Cantera, tkinter, and matplotlib packages must all be installed before running the file.

Please download and run the 'Programming Simulation Project' file and play around with the sliders to create unique test parameters to get an overview of the engine simulation with those inputs. If your inputs are not suitable for combustion with this type of engine, a warning will be displayed to indicate which parameters need to be changed in order to facilitate combustion. Sharp peaks in the plots indicate good combustion in the reaction environment. Short curves suggests incomplete combustion and the warning box should give suggestions for improving the quality of the reaction inputs.

Depending on what kind of computer you are using, the GUI display might cut off parts of the plots or the gauges. If this happens you may have to edit the window size in the code. There is a box and comments that indicate which line you will have to edit. Try reducing the width and height from 400 to 300 or 200.
