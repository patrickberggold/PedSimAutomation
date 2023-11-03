# PedSimAutomation Dynamo Script

This document details the dynamo script used in the repository [_PedSimAutomation_](https://github.com/patrickberggold/PedSimAutomation/).
A screenshot of the script is presented below. ![Cannot find screenshot of script. Make sure it is in the same folder.](script_screenshot.png)

The script is divided into two code paths: _Geometry Creation_ and _Forward Pass_.
Switching between both paths can be done via the first setting of the Forward Pass path: _CreateFloorPlanWithOverlaidZones_, shown in a screenshot below. ![Cannot find image. Make sure it is in the same folder.](CreateFloorPlanWithOverlaidZones.png)

## Geometry Creation

The geometry creation section of this code is used to create Revit geometries. These geometries can then be exported as IFC files.

### Settings: Geometry

The input parameters for this section can be found in the group _Settings: Geometry_. These parameters are summarized below.

| Parameter                   | Description                                                                                                                                                                                          |
| :-------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Default Exterior Wall Types | Type used for external boundaries of geometry                                                                                                                                                        |
| Default Floor Types         | Type used for all floors (or ceilings) in geometry                                                                                                                                                   |
| Default Interior Wall Types | Type used for all interior walls of geometry                                                                                                                                                         |
| Geometry Shape              | Switch between the numbers to generate different geometries. Refer to the script for the geometry types. Note: Geometries 1, 2, and 3 can only be generated when the _Number of Levels_ is set to 1. |
| Number of Levels            | Number of levels in the geometry. Increasing the value of this variable beyond 1 will result in the generation of stairs for geometries 4, 5, and 6.                                                 |
| Length of Site              | Size of geometry in the x-direction (in meters)                                                                                                                                                      |
| Width of Site               | Size of geometry in the y-direction                                                                                                                                                                  |
| Height of Site              | **Deprecated:** **Height of each level is set to 2.5 meters.** Total height of geometry.                                                                                                             |
| Corridor Width              | Width of corridor (in meters)                                                                                                                                                                        |
| Num. Rooms Short Side       | **Non-edge variants**: Number of rooms in the lower side. **Edge variants**: Length of room (in meters).                                                                                             |
| Num. Rooms Long Side        | **Non-edge variants**: Number of rooms in the upper side. **Edge variants**: Number of rooms per side.                                                                                               |
| Door Width                  | Width of door (in meters)                                                                                                                                                                            |
| Obstacle Width              | Width of obstacles (in meters)                                                                                                                                                                       |
| Room Width                  | Width of room (in meters)                                                                                                                                                                            |
| Include Bottleneck          | **Boolean**: Includes a bottleneck, i.e. an obstruction (either by a wall blocking a specific path or reducing the available space for agents to pass through ) if set to _True_.                    |

### Preprocessor Scripts
