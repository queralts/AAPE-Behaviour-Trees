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
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor

    async def run(self):
        try:
            sensor = self.rc_sensor
            central = sensor.central_ray_index

            left_rays  = range(0, central)
            right_rays = range(central + 1, sensor.num_rays)

            def free_space(indices):
                total = 0
                for i in indices:
                    dist = sensor.sensor_rays[Sensors.RayCastSensor.DISTANCE][i]
                    total += sensor.ray_length if dist == -1 else dist
                return total

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

            # Sin parámetros y sin all_rays
            if max_consecutive_hits() < 2:
                return True

            # Decidir hacia dónde girar
            left_space  = free_space(left_rays)
            right_space = free_space(right_rays)

            if left_space == right_space:
                action = random.choice(["tr", "tl"])
            elif right_space > left_space:
                action = "tr"
            else:
                action = "tl"

            # Girar con timeout máximo
            await self.a_agent.send_message("action", action)
            max_time = 2.0
            elapsed = 0.0
            while elapsed < max_time:
                await asyncio.sleep(0.2)
                elapsed += 0.2
                if max_consecutive_hits() < 2:
                    break

            await self.a_agent.send_message("action", "nt")
            return True

        except asyncio.CancelledError:
            await self.a_agent.send_message("action", "nt")
            return False

class GoToFlower:
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
                    
                    if not flower_found:
                        return False
                    
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

                    await asyncio.sleep(0.1)

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

class ReturnToBase:
    def __init__(self, a_agent):
        self.a_agent = a_agent

    async def run(self):
        try:
            print("RETURNING TO BASE")
            await self.a_agent.send_message("action", "teleport_to,BaseAlpha")
            await asyncio.sleep(1.0)  # esperar a que llegue
            print("UNLOADING FLOWERS")
            await self.a_agent.send_message("action", "leave,AlienFlower,2")
            await asyncio.sleep(0.5)
            return True
        except asyncio.CancelledError:
            return False