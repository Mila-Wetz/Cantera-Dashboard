# Cantera-Dashboard
By: Sebastian Riley, Sachin Nair, Mila Wetz

This dashboard is a visual learning tool that allows users to observe how changing various parameters influences the performance of a 4-cylinder internal combustion engine.

The simulation continuously updates as the slider values are changed to increase or decrease factors such as:

  -Injection timing
  -Air to fuel ratio
  -Air Intake Pressure
  -Throttle levels

<img src=https://github.com/Mila-Wetz/Cantera-Dashboard/assets/143420424/fe6fec8e-298a-472a-9623-52229cc4a56d width ="500" height="400">

The code then uses the user input data from the sliders to simulate the engine with those parameters. It then plots the changes in cylinder pressure vs crank angle and volume and calculate engine performance factors such as:

  -Horsepower
  -Adiabatic Heat Release
  -Efficiency
  -Air-to-Fuel Ratio

<img src=https://github.com/Mila-Wetz/Cantera-Dashboard/assets/143420424/95dd7daf-61f3-497b-9ab1-ab9a86a186cf width="400" height="400">
<img src=https://github.com/Mila-Wetz/Cantera-Dashboard/assets/143420424/f62d9cd1-7fd9-4524-b204-ef9bfc112713 width="500" height="400">

Simply run the file and adjust the sliders to match your test parameters to get an overview of the engine simulation with those inputs. If your inputs are not suitable for combustion with this type of engine, a warning will be displayed to indicate which parameters need to be changed in order to facilitate combustion.

Depending on what kind of computer you are using, the GUI display might cut off parts of the plots or the gauges. If this happens you may have to edit the window size in the code. There is a box and comments that indicate which line you will have to edit. Try reducing the size of the x and y coordinates from 300 to 200.
