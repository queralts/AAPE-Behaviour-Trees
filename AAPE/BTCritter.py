import asyncio
import random
#from matplotlib.pylab import full
import py_trees as pt
import Goals_BT_Basic
import Sensors

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

class BTCritter:

    def __init__(self, critter):
        self.root = BN_Avoid(critter)
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