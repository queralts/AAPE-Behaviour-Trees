import math
import random
import asyncio
import Sensors
from collections import Counter

def calculate_distance(point_a, point_b):
    distance = math.sqrt((point_b['x'] - point_a['x']) ** 2 +
                         (point_b['y'] - point_a['y']) ** 2 +
                         (point_b['z'] - point_a['z']) ** 2)
    return distance

class DoNothing:
    """
    Does nothing
    """
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state

    async def run(self):
        print("Doing nothing")
        await asyncio.sleep(1)
        return True

class ForwardStop:
    """
        Moves forward till it finds an obstacle. Then stops.
    """
    STOPPED = 0
    MOVING = 1
    END = 2

    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state
        self.state = self.STOPPED

    async def run(self):
        try:
            while True:
                if self.state == self.STOPPED:
                    # Start moving
                    await self.a_agent.send_message("action", "mf")
                    self.state = self.MOVING
                elif self.state == self.MOVING:
                    sensor_hits = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.HIT]
                    if any(ray_hit == 1 for ray_hit in sensor_hits):
                        self.state = self.END
                        await self.a_agent.send_message("action", "stop")
                    else:
                        await asyncio.sleep(0)
                elif self.state == self.END:
                    break
                else:
                    print("Unknown state: " + str(self.state))
                    return False
        except asyncio.CancelledError:
            print("***** TASK Forward CANCELLED")
            await self.a_agent.send_message("action", "stop")
            self.state = self.STOPPED

class ForwardDist:
    """
        Moves forward a certain distance specified in the parameter "dist".
        If "dist" is -1, selects a random distance between the initial
        parameters of the class "d_min" and "d_max"
    """
    STOPPED = 0
    MOVING = 1
    END = 2

    def __init__(self, a_agent, dist, d_min, d_max):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state
        self.original_dist = dist
        self.target_dist = dist
        self.d_min = d_min
        self.d_max = d_max
        self.starting_pos = dict(self.a_agent.i_state.position)
        self.state = self.STOPPED

    async def run(self):
        try:
            previous_dist = 0.0  # Used to detect if we are stuck
            while True:
                if self.state == self.STOPPED:
                    # starting position before moving
                    self.starting_pos = dict(self.a_agent.i_state.position)
                    # Before start moving, calculate the distance we want to move
                    if self.original_dist < 0:
                        self.target_dist = random.randint(self.d_min, self.d_max)
                    else:
                        self.target_dist = self.original_dist
                    # Start moving
                    await self.a_agent.send_message("action", "mf")
                    self.state = self.MOVING
                    print("TARGET DISTANCE: " + str(self.target_dist))
                elif self.state == self.MOVING:
                    # If we are moving
                    await asyncio.sleep(0.5)  # Wait for a little movement
                    current_dist = calculate_distance(self.starting_pos, self.i_state.position)
                    print(f"Current distance: {current_dist}")
                    if current_dist >= self.target_dist:  # Check if we already have covered the required distance
                        await self.a_agent.send_message("action", "stop")
                        self.state = self.STOPPED
                        return True
                    elif abs(previous_dist - current_dist) < 0.001:  # We are not moving
                        print(f"previous dist: {previous_dist}, current dist: {current_dist}")
                        print("NOT MOVING")
                        await self.a_agent.send_message("action", "stop")
                        self.state = self.STOPPED
                        return False
                    previous_dist = current_dist
                else:
                    print("Unknown state: " + str(self.state))
                    return False
        except asyncio.CancelledError:
            print("***** TASK Forward CANCELLED")
            await self.a_agent.send_message("action", "ntm")
            self.state = self.STOPPED

class Turn:
    """
    Repeats the action of turning a random number of degrees in a random
    direction (right or left)
    """
    LEFT = -1
    RIGHT = 1

    SELECTING = 0
    TURNING = 1

    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state

        self.current_heading = 0
        self.new_heading = 0

        self.state = self.SELECTING

    async def run(self):
        try:
            while True:
                if self.state == self.SELECTING:
                    print("SELECTING NEW TURN")
                    rotation_direction = random.choice([-1, 1])
                    print(f"Rotation direction: {rotation_direction}")
                    rotation_degrees = random.uniform(1, 180) * rotation_direction
                    print("Degrees: " + str(rotation_degrees))
                    current_heading = self.i_state.rotation["y"]
                    print(f"Current heading: {current_heading}")
                    self.new_heading = (current_heading + rotation_degrees) % 360
                    if self.new_heading == 360:
                        self.new_heading = 0.0
                    print(f"New heading: {self.new_heading}")
                    if rotation_direction == self.RIGHT:
                        await self.a_agent.send_message("action", "tr")
                    else:
                        await self.a_agent.send_message("action", "tl")
                    self.state = self.TURNING
                elif self.state == self.TURNING:
                    # check if we have finished the rotation
                    current_heading = self.i_state.rotation["y"]
                    diff = abs(current_heading - self.new_heading)
                    final_condition = min(diff, 360 - diff)
                    if final_condition < 5:
                        await self.a_agent.send_message("action", "nt")
                        current_heading = self.i_state.rotation["y"]
                        print(f"Current heading: {current_heading}")
                        print("TURNING DONE.")
                        self.state = self.SELECTING
                        return True
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            print("***** TASK Turn CANCELLED")
            await self.a_agent.send_message("action", "nt")

class GoToFlower():
    DETECTING = 0
    TURNING = 1
    MOVING = 2

    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state
        self.threshold = 1.5
        self.sensor_obj_info = self.a_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        self.state = self.DETECTING
        self.detecting_attempts = 0     
        self.max_detecting_attempts = 10  

    async def run(self):
        try:
            print("GO TO FLOWER STARTED")
            while True:
                if self.state==self.DETECTING:

                    print("DETECTING FLOWER")
                    flower_found = False
                    sensor_obj_info = self.a_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
                    
                    for index, value in enumerate(sensor_obj_info):
                        if value:
                            if value['tag'] == 'AlienFlower':
                                flower_found = True
                                # Get ray angle and current rotation in y
                                self.angle = self.a_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.ANGLE][index]
                                current_rotation = self.i_state.rotation['y']
                                # Compute world heading we need to reach
                                self.target_heading = (current_rotation + self.angle) % 360
                                self.state = self.TURNING
                                break
                    
                    await asyncio.sleep(0)

                elif self.state==self.TURNING:
                    print("TURNING TOWARDS FLOWER")

                    sensor_obj_info = self.a_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]

                    flower_found = False

                    for index, value in enumerate(sensor_obj_info):
                        if value and value["tag"] == "AlienFlower":

                            flower_found = True

                            angle = self.a_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.ANGLE][index]

                            if abs(angle) < 8:
                                await self.a_agent.send_message("action", "nt")
                                await self.a_agent.send_message("action", "mf")
                                self.state = self.MOVING
                            elif angle > 0:
                                await self.a_agent.send_message("action", "tr")
                            else:
                                await self.a_agent.send_message("action", "tl")

                            break

                    if not flower_found:
                        await self.a_agent.send_message("action", "nt")
                        return False

                    await asyncio.sleep(0)

                elif self.state == self.MOVING:
                    print("MOVING TOWARDS FLOWER")

                    flower_found = False
                    reached = False

                    sensor_obj_info = self.a_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
                    
                    for index, value in enumerate(sensor_obj_info):
                        if value:
                            if value["tag"] == 'AlienFlower':
                                
                                flower_found = True
                                
                                distance = self.a_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.DISTANCE][index]
                                
                                if distance < self.threshold:
                                    reached = True
                                
                                break
                    
                    # Check if we reached the flower or already picked it
                    if reached or not flower_found:
                        await self.a_agent.send_message("action", "ntm")
                        return True
                    
                    # Flower found but still far
                    await asyncio.sleep(0)

        except asyncio.CancelledError:
            print("***** TASK GoToFlower CANCELLED")
            await self.a_agent.send_message("action", "nt")
            await self.a_agent.send_message("action", "stop")