from roboflow import Roboflow
rf = Roboflow(api_key="5uZWFhXLBSy9gVfwzdU9")
project = rf.workspace("fallen-people-data-set").project("fallen-person-uhif8")
version = project.version(2)
dataset = version.download("yolov5")
                
                