import asyncio
import random
#from matplotlib.pylab import full
import py_trees as pt
import Goals_BT_Basic
import Sensors
from py_trees.display import render_dot_tree


class BN_Avoid(pt.behaviour.Behaviour):

    def __init__(self, aagent):
        super().__init__("BN_Avoid")
        self.agent = aagent
        self.goal = None

    def initialise(self):
        self.goal = asyncio.create_task(Goals_BT_Basic.Avoid(self.agent).run())

    def update(self):
        if not self.goal.done():
            return pt.common.Status.RUNNING
        else:
            return pt.common.Status.SUCCESS

    def terminate(self, new_status):
        if self.goal and not self.goal.done():
            self.goal.cancel()


class BN_DetectAstronaut(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        # print("Initializing BN_DetectAstronaut")
        super(BN_DetectAstronaut, self).__init__("BN_DetectAstronaut")
        self.my_agent = aagent

    def initialise(self):
        pass

    def update(self):
        sensor_obj_info = self.my_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        for index, value in enumerate(sensor_obj_info):
            if value:  # there is a hit with an object
                if value["tag"] == "Astronaut":  # If it is an astronaut
                    # print("Astronaut detected!")
                    #print("BN_DetectAstronaut completed with SUCCESS")
                    return pt.common.Status.SUCCESS
        # print("No Astronaut...")
        # print("BN_DetectAstronaut completed with FAILURE")
        return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        pass    

class BN_ChaseAstronaut(pt.behaviour.Behaviour):
    
    def __init__(self, aagent):
        super().__init__("BN_ChaseAstronaut")
        self.agent = aagent
        self.goal = None

    def initialise(self):
        self.goal = asyncio.create_task(Goals_BT_Basic.ChaseAstronaut(self.agent).run())

    def update(self):
        if not self.goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status):
        if self.goal and not self.goal.done():
            self.goal.cancel()    

class BTCritter:

    def __init__(self, critter):

        chase = pt.composites.Sequence("Chase", memory=True)
        chase.add_children([BN_DetectAstronaut(critter), BN_ChaseAstronaut(critter)])
        
        roam = BN_Avoid(critter)

        self.root = pt.composites.Selector("BTCritter", memory=False)
        self.root.add_children([chase, roam])
        self.behaviour_tree = pt.trees.BehaviourTree(self.root)

        # render_dot_tree(self.root)
        
    def stop_behaviour_tree(self):
        print("Stopping the BehaviorTree")
        try:
            self.root.tick_once()
        except:
            pass 

        for node in self.root.iterate():
            if node.status != pt.common.Status.INVALID:
                node.status = pt.common.Status.INVALID
                # For nodes that weren't RUNNING, manually call terminate
                if hasattr(node, "terminate"):
                    node.terminate(pt.common.Status.INVALID)

    async def tick(self):
        self.behaviour_tree.tick()
        await asyncio.sleep(0)