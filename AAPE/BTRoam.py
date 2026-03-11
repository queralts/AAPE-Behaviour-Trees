import asyncio
import random
from matplotlib.pylab import full
import py_trees as pt
import Goals_BT_Basic
import Sensors

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

class BN_ForwardRandom(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        # print("Initializing BN_ForwardRandom")
        super(BN_ForwardRandom, self).__init__("BN_ForwardRandom")
        self.logger.debug("Initializing BN_ForwardRandom")
        self.my_agent = aagent

    def initialise(self):
        self.logger.debug("Create Goals_BT.ForwardDist task")
        self.my_goal = asyncio.create_task(Goals_BT_Basic.ForwardDist(self.my_agent, 0.6, 3, 6).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                self.logger.debug("BN_ForwardRandom completed with SUCCESS")
                # print("BN_ForwardRandom completed with SUCCESS")
                return pt.common.Status.SUCCESS
            else:
                self.logger.debug("BN_ForwardRandom completed with FAILURE")
                # print("BN_ForwardRandom completed with FAILURE")
                return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        # Finishing the behaviour, therefore we have to stop the associated task
        self.logger.debug("Terminate BN_ForwardRandom")
        self.my_goal.cancel()


class BN_Turn(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        # print("Initializing BN_Turn")
        super(BN_Turn, self).__init__("BN_Turn")
        self.my_agent = aagent

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT_Basic.Turn(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            res = self.my_goal.result()
            if res:
                # print("BN_Turn completed with SUCCESS")
                return pt.common.Status.SUCCESS
            else:
                # print("BN_Turn completed with FAILURE")
                return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        # Finishing the behaviour, therefore we have to stop the associated task
        self.logger.debug("Terminate BN_Turn")
        self.my_goal.cancel()

class BN_DetectObstacle(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_DetectObstacle, self).__init__("BN_DetectObstacle")
        self.my_agent = aagent

    def initialise(self):
        pass

    def update(self):
        # # Si ya está girando, no interrumpir
        # if self.my_agent.i_state.isRotatingRight or self.my_agent.i_state.isRotatingLeft:
        #     return pt.common.Status.RUNNING  # deja que el Turn actual termine

        sensor = self.my_agent.rc_sensor

        def max_consecutive_hits():
            max_consec = 0
            current = 0
            for i in range(sensor.num_rays):
                hit = sensor.sensor_rays[Sensors.RayCastSensor.HIT][i]
                obj_info = sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO][i]
                is_flower = obj_info and obj_info.get("tag") == "AlienFlower"
                if hit and not is_flower:
                    current += 1
                    max_consec = max(max_consec, current)
                else:
                    current = 0
            return max_consec

        if max_consecutive_hits() >= 2:  
            print("Obstacle detected!")
            return pt.common.Status.SUCCESS
            
        return pt.common.Status.FAILURE

    def terminate(self, new_status: pt.common.Status):
        pass

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

class BTRoam:
    def __init__(self, aagent):
        # py_trees.logging.level = py_trees.logging.Level.DEBUG

        self.aagent = aagent

        # VERSION 1
        # self.root = pt.composites.Sequence(name="Sequence", memory=True)
        # self.root.add_children([BN_Turn(aagent),
        #                         BN_ForwardRandom(aagent),
        #                         BN_DoNothing(aagent)])

        # VERSION 2
        # self.root = pt.composites.Parallel("Parallel", policy=py_trees.common.ParallelPolicy.SuccessOnAll())
        # self.root.add_children([BN_ForwardRandom(aagent), BN_Turn(aagent)])

        # VERSION 3 (with DetectFlower)

        detection = pt.composites.Sequence(name="DetectFlower", memory=True)
        detection.add_children([BN_DetectFlower(aagent), BN_GoToFlower(aagent)])

        # Si hay obstáculo → girar 
        obstacle = pt.composites.Sequence("Obstacle", memory=False)
        obstacle.add_children([BN_DetectObstacle(aagent), BN_Turn(aagent)])

        # Si no hay obstáculo → avanzar
        roaming = pt.composites.Selector("Roaming", memory=False)
        roaming.add_children([obstacle, BN_ForwardRandom(aagent)])

        # Inventario lleno → volver a base
        full = pt.composites.Sequence("Full", memory=True)
        full.add_children([BN_CheckInventoryFull(aagent), BN_ReturnToBase(aagent)])

        # Si no está lleno → detectar flor o deambular
        not_full = pt.composites.Selector("NotFull", memory=False)
        not_full.add_children([detection, roaming])

        self.root = pt.composites.Selector(name="Selector", memory=False)
        self.root.add_children([full, not_full])

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

