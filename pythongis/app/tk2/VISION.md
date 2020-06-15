Tk2

All normal widgets are implemented with wrappers. 
In addition they have improved event binding methods incl temporary ones. 
All widgets have method to support right click popup menu. 
And new motion animations, as well as entry and exit. 

Buttons and labels have easier icon settings, incl option for gradient background. 
All frames and canvases have auto scroll. 
Frames have method to add additional frames that share space (pane separated). 
Frames have method to add widget groupings (separator).
Frames, labels, and buttons have option to be draggable when toggled (like a toolbar).
Labels have method to allow editing text content on second click, ala Windows. 
Improved slider. 

New multichoice and multientry for many common input use cases. 
New ribbon widget. 
New quick popup windows with autofocus and cancel/ok buttons and keyboard shortcuts. 
New smooth and arrangeable vertical listbox based on widget items and moving animations. 
New progbar. 

New calendar widget. 
New graphics renderer (with built in navigation based on pyagg, and draw point,line,poly mode).
Maybe photoshow widget. 
Maybe simple but memory light table widget. 

Uses ttk where possible for better style. To make all compatible,
allow tk options by simply creating new style behind the scene,
and allow ttk style by having a style handler that stores, looks up,
and uses the options saved to a style name. 

