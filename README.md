<div id="top"></div>

<!-- PROJECT LOGO -->
<br />
<div align="center">

  <h3 align="center">Towards predicting Pedestrian Evacuation Time and Density from Floorplans using a Vision Transformer</h3>

  <p align="center">
    Chair of Modelling and Simulation - Technical University of Munich.
    <br />
    Berggold, P., and Hassaan, M.
    <br />
    <a href=#docs><strong>Explore the docs »</strong></a>
    <!-- <strong>[Explore the docs »](#documentation)</strong> -->
    <br />
    <br />
    <a href="mailto:patrick.berggold@tum.de">Report Bug</a>
    ·
    <a href="mailto:patrick.berggold@tum.de">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#docs">Documentation</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

Project title: Towards predicting Pedestrian Evacuation Time and Density from Floorplans using a Vision Transformer

In this work, we propose a deep learning-based approach to realistically and instantly predict pedstrian densities over time and total evacuation time from office building layouts and simulation input parameters.
The aim of our approach is to integrate the neural network into the BIM-driven building design process to get a good estimate of how safely a building is designed with respect to pedestrian safety. Since pedestrian simulations entail long runtimes and laborious export and conversion steps, our approach delivers such predictions much faster, such that it can be used to interrogate the many design variants that come up particularly during the early stages of the project.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

Start by confirming Git is installed on your computer

```sh
git --version
```

You should get an output similar to the one below, otherwise download and install [Git](https://git-scm.com/downloads).

```sh
git version 1.2.3
```

Next clone the repository:

```sh
git clone https://github.com/patrickberggold/PedSimAutomation
```

### Folder Strcture

Once you clone the repository, make sure the folder structure matches the directory tree shown below.

📦PedSimAutomation  
┣ 📂DynamoDependencies  
┃ ┣ 📜python_environment_packages.txt  
┣ 📂DynamoScripts  
┃ ┣ 📜MainWithInferenceWithoutTraining.dyn  
┣ 📂TrainingScripts
┃ ┣ 📜datamodule.py
┃ ┣ 📜dataset.py
┃ ┣ 📜helper.py
┃ ┣ 📜image_module.py
┃ ┣ 📜main.py
┃ ┣ 📜model.py 
┣ 📂ExampleDataset 
┃ ┣ 📂inputs
┃ ┣ 📂targets
┣ 📜.gitignore  
┗ 📜README.md

### Revit

Make sure you have Revit installed on your machine.
Details on how to install Revit can be found [here](https://www.autodesk.com/products/revit/).

## Initial Setup

#### Python version

Before using this script, in Revit, open Dynamo (Manage -> Dynamo), and create a temporary script with one python node.
Include the code below in the python node to find Revit's python version.

```
import sys

OUT = sys.version
```

The output of this node is the Revit's python version. It should look something like this.

```
1.23.45
```

**Warning**: This code does not support Python 2.0. If you are using an older version of Revit, the default may be python 2.0. Make sure you select Python 3.0 before running the python node.

Install this python version and use it to create a virtual environment using the command shown below.
You can find information on how to download python [here](https://wiki.python.org/moin/BeginnersGuide/Download), and some useful information on virtual environments [here](https://docs.python.org/3/library/venv.html#creating-virtual-environments).

```
python3 -m venv /path/and/name/of/your/virtual/environment/
```

After activating your virtual environment, navigate to the directory /DynamoDependencies/ and open your preferred CLI.
Use it to install all the required python libraries by running the following command (shown for both Pip and Anaconda).

- Pip

```
pip install -r python_environment_packages.txt
```

- Anaconda

```
conda install --file python_environment_packages.txt
```

<!-- USAGE EXAMPLES -->

## Usage

Start by creating a new Revit file, and opening Dynamo (Manage -> Dynamo).
Then navigate to the directory /DynamoScripts/ and open the file MainWithInferenceWithoutTraining.dyn.

**Note**: We recommend using metric units to avoid potential errors.

Three types of geometries can be created using this script, named here as Cross, EndToEnd(E2E), and Edge.
You can change the geometry by editing the slider: "Geometry Shape".

Once you select your geometry type, fill in the rest of the input parameters - including all required paths - and make sure the node "CreateFloorPlanWithOverlaidZones" is set to False, then run the script.

The output of the script should be a floor plan of the geometry.
You can now switch the node "CreateFloorPlanWithOverlaidZones" to True and rerun the script.
This will generate the floor plan image and overlay it with the colors of the sources and destinations.
This image is then fed as an input to the transformer.

Once the execution is complete, you should see a .gif, showing the predicted frames of the transformer, in your chosen export path.

## Documentation

<div id = "docs"></div>

_Details of all scripts and classes can be found in
[Documentation Link Placeholder](https://github.com/patrickberggold/PedSimAutomation)._

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

If you have any questions with regards to our research or the usage of this project, please don't hesitate to contact us via an email. We will update more information regarding the usage and training of the network in the next few days.

Patrick Berggold - patrick.berggold@tum.de

Mohab Hassaan - mohab.hassaan@tum.de

Project Link: [https://github.com/patrickberggold/PedSimAutomation](https://github.com/patrickberggold/PedSimAutomation)

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/othneildrew/Best-README-Template/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/othneildrew/Best-README-Template/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/othneildrew
[product-screenshot]: images/screenshot.png
