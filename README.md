# StructureTools - alpha

![](https://github.com/maykowsm/StructureTools/blob/main/freecad/StructureTools/resources/ui/img/img-1.png)

This is a workbench for FreeCAD that implements a set of tools for modeling and analyzing structural stresses, similar to analysis software such as SAP2000, Cype3D, SkyCiv, EdiLus, among many others.

The goal is to provide engineers and engineering students with a powerful and easy-to-use open source tool. Fully integrated with the existing tools in FreeCAD.

**Note:** The tools developed are limited to modeling, calculation and analysis of stresses in structural elements. The focus is not on developing tools for dimensioning these elements. The dimensioning will be handled by another workbench that I am developing in parallel to this one.

## screenshots

![](https://github.com/maykowsm/StructureTools/blob/main/freecad/StructureTools/resources/screenshots/galpao.png)

![](https://github.com/maykowsm/StructureTools/blob/main/freecad/StructureTools/resources/screenshots/viga2D.png)
![](https://github.com/maykowsm/StructureTools/blob/main/freecad/StructureTools/resources/screenshots/vigas3D.png)
![](https://github.com/maykowsm/StructureTools/blob/main/freecad/StructureTools/resources/screenshots/portico3D.png)
![image](https://github.com/user-attachments/assets/b59c8e6b-39f4-4499-8f17-8ab3a676485a)
![image](https://github.com/user-attachments/assets/49a95a44-0871-43af-80db-6a8705ad25ab)
![image](https://github.com/user-attachments/assets/3fc213eb-336f-4926-9b6b-e3b78e68d1bb)

Draftly count the weight of steel structure members
![image](https://github.com/user-attachments/assets/fa75b532-2ef5-4548-a4e9-991591342804)






## Installing

At the moment, the StructureTools workbench can only be installed manually. I am working on getting the workbench into the FreeCAD repository.

To manually install the workbench, follow these steps:

1. Click on the “Code” button and then on Download ZIP.

2. Unzip the ZIP file to your computer.

3. Rename the extracted folder to “StructureTools.”

4. Copy the renamed folder to the Mod folder inside your FreeCAD default installation folder.

For more details on manual installation, watch the video:
https://www.youtube.com/watch?v=HeYGVXhw31A


## Tools

The StructureTools workbench is still under development and is constantly changing with the addition of new tools, improvements and bug fixes, I will try to keep this list updated whenever possible.

**Define Member** - modeling of bar elements, the graphical modeling of a bar element can be done using the Draft tool through the line tool and later converting it into a member of the structure. With the definition of the member of the structure done, it is possible to assign to this member several parameters such as Section, Material, and whether it is a truss member.

**Support** - modeling of the supports of the structure capable of fixing the individual rotation and translation of the X, Y and Z axes.

**Section** - defines the section of the members of the structure, capable of capturing the geometric parameters of the area of ​​any face.

**Material** - Defines the physical properties of the material of the structural elements.

**Distributed Load** - defines an external linear load distributed on a member of the structure, capable of modeling uniformly distributed loads, triangular and trapezoidal loads, definition in the global axis.

**Nodal Load** – defines an external force acting on a node of the structure, defined on the global axis.

**Calc Structure** – a tool that creates a calculation object with all the results of the efforts of the structural elements, bending moment, shear, axial force, torque and displacements. It is possible to change the units of the results, number of points calculated for each element, automatic calculation of own weight.

**Diagram** – generates the effort diagrams based on the Calc object. With this tool, it is possible to graphically view the diagram of the efforts of the same on the axis of the element itself. The tool has parameters for scale, color, text size, all to facilitate the visualization and interpretation of the results. It is possible to draw the diagram of individual elements or of the entire structure.

## Additional tools

**Copy load value** –  With this tool, to copy value from distribute selected one to others --> reduce time for change one by one

**Copy member properties** –  With this tool, to copy assigment section & material from selected one to others --> reduce time for change one by one

**Copy assignment support** –  With this tool, to copy assigment section & material from selected one to others --> reduce time for change one by one

![image](https://github.com/user-attachments/assets/0ae870d8-34d9-40dd-8e81-1b4649ffd968)

**Import section** –   to import section properties from txt file to model (not need to define section from sketch). Also can self-make a library section propeties and once need then load to model. Format section properties see snapshot below

![image](https://github.com/user-attachments/assets/9e991e05-20f3-4022-bd3a-e4843d35a1e1)



You can see more about the tools in these videos:

* StructureTools - Alpha Version - Workbench Tools and Workflow: https://www.youtube.com/watch?v=AicdjiOc61k
* StructureTools - Alpha Version - Calculation of forces of simply supported beams: https://www.youtube.com/watch?v=Ig0SyqJao0Q
* StructureTools -  Structure Tool in Freecad: how to use? (https://github.com/chantran22/StructureTools_replica/blob/main/docs/struc_tool.pdf)
* StructureTools - Demo model examples (https://github.com/chantran22/StructureTools_replica/blob/main/docs/New%20folder/)

## Development
You can follow the development of the project here: https://github.com/users/maykowsm/projects/1/views/1
I'm trying to write proper documentation for the FreeCAD Wiki, if you want to help me, you'll be welcome.

You can also follow the discussion about StructureTools on the FreeCAD forum: https://forum.freecad.org/viewtopic.php?t=94995

Please consider supporting the project so I can dedicate more time to it: [  Patreon  ](https://patreon.com/StructureTools), [  ApoiaSe  ](  https://apoia.se/structuretools  )

## Dependencies

['numpy','scipy','prettytable','PyniteFEA']

## Maintainer

Maykow Menezes

[linkedin](https://www.linkedin.com/in/engmaykowmenezes/)

[X old twitter](https://x.com/StructureTools)

Telegram: @Eng_Maykow_Menezes

eng.maykowmenezes@gmail.com
