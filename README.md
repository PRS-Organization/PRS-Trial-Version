# PRS-Trial-Version
Trial version for prs platform (python project). Please note that the complete experience requires downloading the Unity resource.
The complete API documentation and task benchmark is comming soon!

## Quick Start Guide for PRS Platform Demo

Follow these steps to quickly set up and run the PRS demo:

1. Clone the PRS demo repository:  
```
    git clone https://github.com/PRS-Organization/PRS-Trial-Version.git
```  
2. Ensure you have a Python virtual environment (Python version >= 3.9) activated.

3. Install the required Python packages:  
```
    pip install -r prs_requirements.txt
```
4. Download the Unity executable file (Ubuntu version) from [Google Drive](https://drive.google.com/file/d/1-EjHIvCVAeiMFxyY6JbjvVrzVO0xvn0m/view?usp=sharing) and save it as `prs_unity_demo.rar`.

5. Extract the `prs_unity_demo.rar` file into the project folder:  
```
	unrar x prs_unity_demo.rar
```   
Note: This should create a `unity` folder. Give it necessary permissions:  
```
	sudo chmod 777 -R unity
```
6. Start running the demo:  
```
	python prs_demo.py
```     
or start with only unity application: 
``` 
    bash start.sh 
```
7. If you encounter a port occupation error, run:  
```
	bash clean_port.sh
```
8. After running the Python script, you can open another terminal and execute ```start.sh``` or directly run `unity/PRS.x86_64`.

9. Wait a few seconds for Unity to render the graphics.

10. In Unity, you can control the camera movement using the keyboard keys W, A, S, D, Q, and E.

11. To close the demo, first close the Unity program (or press Esc), then stop the Python program (Ctrl+C or Ctrl+Z), and finally run:  
 ```
	bash clean_port.sh
 ```  
Note: In this version, there's no function to end the environment due to its long-running nature.

12. Please note that this is just a test demo, and there is no interactive behavior in the environment.

Stay tuned for the upcoming complete API documentation and task benchmarks!

## More API Guidance
[NPC API](document/api.md)

