import asyncio

#from matplotlib.pylab import full
import py_trees as pt
import Goals_BT_Basic
import Sensors

from py_trees.display import render_dot_tree

class BN_DoNothing(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_agent = aagent
        self.my_goal = None
        # print("Initializing BN_DoNothing")
        super(BN_DoNothing, self).__init__("BN_DoNothing")

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.DoNothing(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                # print("BN_DoNothing completed with SUCCESS")
                return pt.common.Status.SUCCESS
            else:
                # print("BN_DoNothing completed with FAILURE")
                return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        # Finishing the behaviour, therefore we have to stop the associated task
        self.my_goal.cancel()


class BN_AvoidObstacle(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        super(BN_AvoidObstacle, self).__init__("BN_AvoidObstacle")
        self.my_agent = aagent

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.AvoidObstacle(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            return pt.common.Status.SUCCESS if self.my_goal.result() else pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        self.my_goal.cancel()

class BN_DetectFlower(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        # print("Initializing BN_DetectFlower")
        super(BN_DetectFlower, self).__init__("BN_DetectFlower")
        self.my_agent = aagent

    def initialise(self):
        pass

    def update(self):
        sensor_obj_info = self.my_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        for index, value in enumerate(sensor_obj_info):
            if value:  # there is a hit with an object
                if value["tag"] == "AlienFlower":  # If it is a flower
                    print("Flower detected!")
                    print("BN_DetectFlower completed with SUCCESS")
                    return pt.common.Status.SUCCESS
        print("No flower...")
        print("BN_DetectFlower completed with FAILURE")
        return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        pass


class BN_GoToFlower(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_agent = aagent
        self.my_goal = None
        # print("Initializing BN_GoToFlower")
        super(BN_GoToFlower, self).__init__("BN_GoToFlower")

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.GoToFlower(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                # print("BN_GoToFlower completed with SUCCESS")
                return pt.common.Status.SUCCESS
            else:
                # print("BN_GoToFlower completed with FAILURE")
                return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        # Finishing the behaviour, therefore we have to stop the associated task
        self.my_goal.cancel()


class BN_CheckInventoryFull(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_CheckInventoryFull, self).__init__("BN_CheckInventoryFull")
        self.my_agent = aagent

    def initialise(self):
        pass

    def update(self):
        for item in self.my_agent.i_state.myInventoryList:
            if item.get("name") == "AlienFlower" and item.get("amount") >= 2:
                print("Inventory full!")
                return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        pass

class BN_ReturnToBase(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_ReturnToBase, self).__init__("BN_ReturnToBase")
        self.my_agent = aagent
        self.my_goal = None

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.ReturnToBase(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        self.my_goal.cancel()

class BN_DetectFrozen(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        # print("Initializing BN_DetectInventoryFull")
        super(BN_DetectFrozen, self).__init__("BN_DetectFrozen")
        self.my_agent = aagent
        self.i_state = aagent.i_state

    def initialise(self):
        pass

    def update(self):
        if self.i_state.isFrozen:
            return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE
    
    def terminate(self, new_status: pt.common.Status):
        pass

class BN_DetectCritter(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_DetectCritter")
        self.my_agent = aagent

    def initialise(self): pass

    def update(self):
        sensor_obj_info = self.my_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        for value in sensor_obj_info:
            if value and value["tag"] == "CritterMantaRay":
                print(f"-------Objeto detectado: {value}")
                return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE

    def terminate(self, new_status): pass


class BN_FleeFromCritter(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_FleeFromCritter")
        self.my_agent = aagent
        self.my_goal = None

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.FleeFromCritter(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            return pt.common.Status.SUCCESS if self.my_goal.result() else pt.common.Status.FAILURE

    def terminate(self, new_status):
        self.my_goal.cancel()

class BTRoam:
    def __init__(self, aagent):
        # py_trees.logging.level = py_trees.logging.Level.DEBUG

        self.aagent = aagent

        # VERSION 1 (Alone with avoid)
        # detection = pt.composites.Sequence(name="DetectFlower", memory=True)
        # detection.add_children([BN_DetectFlower(aagent), BN_GoToFlower(aagent)])

        # full = pt.composites.Sequence("Full", memory=True)
        # full.add_children([BN_CheckInventoryFull(aagent), BN_ReturnToBase(aagent)])

        # self.root = pt.composites.Selector(name="BTRoam", memory=False)
        # self.root.add_children([full, detection, BN_AvoidObstacle(aagent)])

        # self.behaviour_tree = pt.trees.BehaviourTree(self.root)
        
        # VERSION 2 (Collect and run)
        frozen = pt.composites.Sequence(name='DetectFrozen', memory=True)
        frozen.add_children([BN_DetectFrozen(aagent), BN_DoNothing(aagent)])

        detection = pt.composites.Sequence(name="DetectFlower", memory=True)
        detection.add_children([BN_DetectFlower(aagent), BN_GoToFlower(aagent)])

        full = pt.composites.Sequence("Full", memory=False)
        full.add_children([BN_CheckInventoryFull(aagent), BN_ReturnToBase(aagent)])

        flee = pt.composites.Sequence("Flee", memory=True)
        flee.add_children([BN_DetectCritter(aagent), BN_FleeFromCritter(aagent)])

        self.root = pt.composites.Selector(name="BTRoam", memory=False)
        self.root.add_children([frozen, flee, full, detection, BN_AvoidObstacle(aagent)])

        self.behaviour_tree = pt.trees.BehaviourTree(self.root)
    
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

