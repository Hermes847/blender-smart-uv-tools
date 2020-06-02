# blender-smart-uv-tools
## Current usages:
- Align UV 
- Extend Selection
- Auto straighten quads and correct texel density
- Correct uv shell texel density
## Highlight
### Straighten Quads
Before:
![](https://raw.githubusercontent.com/Hermes847/images/master/1.png)
After:
![](https://raw.githubusercontent.com/Hermes847/images/master/2.png)
Just one click,the quads will be straightened,the size of each quad depends on the size of its corresponding geometric.

note : this only works for quads
### Correct Texel Density
Before:
![](https://raw.githubusercontent.com/Hermes847/images/master/3.png)
Select one undistorted edge for each uv shell:
![](https://raw.githubusercontent.com/Hermes847/images/master/4.png)
click 'uniform scale'
![](https://raw.githubusercontent.com/Hermes847/images/master/5.png)
you have to select an undistorted edge for each uv shell, but in most cases that will be the longest edge,so I made a operator for you.

### Utils
There is many useful functions in UVGraph class, I'm sure you can make use of it.
