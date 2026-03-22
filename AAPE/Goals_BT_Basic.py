import math
import random
import asyncio
import Sensors
from collections import Counter

## camina como si le estan empujando
## critters deberian girar y forward a la vez, no turn y luego forward

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

                        self.starting_pos = dict(self.i_state.position)
                        if self.original_dist < 0:
                            self.target_dist = random.randint(self.d_min, self.d_max)
                        else:
                            self.target_dist = self.original_dist
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

            await self.a_agent.send_message("action", "stop")
            await asyncio.sleep(0.05)

            # Girar con timeout máximo
            await self.a_agent.send_message("action", action)
            max_time = 2.0
            elapsed = 0.0
            while elapsed < max_time:
                await asyncio.sleep(0.2)
                elapsed += 0.2
                if max_consecutive_hits() < 2:
                    break

            await self.a_agent.send_message("action", "stop")
            return True

        except asyncio.CancelledError:
            await self.a_agent.send_message("action", "stop")
            return False

class GoToFlower:
    DETECTING = 0
    TURNING = 1
    MOVING = 2

    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state
        self.threshold = 0.7
        self.sensor_obj_info = self.a_agent.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        self.state = self.DETECTING
        self.detecting_attempts = 0     
        self.max_detecting_attempts = 10
        self.current_turn = None  

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
                    
                    await asyncio.sleep(0.1)

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
                                if self.current_turn != "tr":
                                    await self.a_agent.send_message("action", "tr")
                                    self.current_turn = "tr"
                            else:
                                if self.current_turn != "tl":
                                    await self.a_agent.send_message("action", "tl")
                                    self.current_turn = "tl"

                            break

                    if not flower_found:
                        await self.a_agent.send_message("action", "nt")
                        return False

                    await asyncio.sleep(0.1)

                elif self.state == self.MOVING:
                    print("MOVING TOWARDS FLOWER")
                    await asyncio.sleep(0.2)


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

class ReturnToBase:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.i_state = a_agent.i_state

    async def run(self):
        try:
            await self.a_agent.send_message("action", "stop")
            print("RETURNING TO BASE BY WALKING")
            await self.a_agent.send_message("action", "walk_to,BaseAlpha")

            # Wait for the navmesh to actually start the route
            # for _ in range(10):
            #     if self.i_state.onRoute:
            #         break
            #     await asyncio.sleep(0.2)
            while self.i_state.onRoute:
                await asyncio.sleep(0.2)

            timeout = 20.0
            elapsed = 0.0
            step = 0.2

            while elapsed < timeout:
                # reached destination
                if not self.i_state.onRoute:
                    break

                await asyncio.sleep(step)
                elapsed += step

            # 15s passed and agent is still returning to base: teleport directly
            if self.i_state.currentNamedLoc != "BaseAlpha" and self.i_state.onRoute:
                print("Teleporting to base")
                await self.a_agent.send_message("action", "teleport_to,BaseAlpha")
                await asyncio.sleep(1.0)

            print("UNLOADING FLOWERS")
            await self.a_agent.send_message("action", "leave,AlienFlower,2")
            await asyncio.sleep(0.5)
            return True

        except asyncio.CancelledError:
            await self.a_agent.send_message("action", "stop")
            return False


class FleeFromCritter:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state

    async def run(self):
        try:
            # Buscar el critter más cercano
            sensor_obj_info = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
            critter_angle = None
            critter_dist = float('inf')

            for index, value in enumerate(sensor_obj_info):
                if value and value["tag"] == "CritterMantaRay":
                    dist = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.DISTANCE][index]
                    if dist < critter_dist:
                        critter_dist = dist
                        critter_angle = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.ANGLE][index]

            if critter_angle is None:
                return False

            # Girar en dirección opuesta al critter
            if critter_angle >= 0:  # critter a la derecha o al frente → girar izquierda
                await self.a_agent.send_message("action", "tl")
            else:  # critter a la izquierda → girar derecha
                await self.a_agent.send_message("action", "tr")

            await asyncio.sleep(1.0)
            await self.a_agent.send_message("action", "stop")

            # Avanzar alejándose
            await self.a_agent.send_message("action", "mf")
            await asyncio.sleep(2.0)
            await self.a_agent.send_message("action", "ntm")

            return True

        except asyncio.CancelledError:
            await self.a_agent.send_message("action", "stop")
            return False
        

class Avoid:
    STOPPED = 0
    MOVING = 1
    AVOIDING = 2

    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor

    def choose_turn_direction(self):
        left_hits = 0
        right_hits = 0

        for index, ray in enumerate(zip(*self.rc_sensor.sensor_rays)):
            if ray[Sensors.RayCastSensor.HIT] == 1:
                if ray[Sensors.RayCastSensor.ANGLE] < 0:
                    left_hits += 1
                elif ray[Sensors.RayCastSensor.ANGLE] > 0:
                    right_hits += 1
        
        if left_hits > right_hits:
            return "right"
        else:
            return "left"
    
    async def turn_until_clear(self):
        turn_direction = self.choose_turn_direction()
        if turn_direction == "left":
            await self.a_agent.send_message("action", "tl")
        else:
            await self.a_agent.send_message("action", "tr")

        while True:
            front_sensors = []
            for index, ray in enumerate(zip(*self.rc_sensor.sensor_rays)):
                if -30 <= ray[Sensors.RayCastSensor.ANGLE] <= 30:
                    front_sensors.append(ray)

            if any(ray[Sensors.RayCastSensor.HIT] == 1 for ray in front_sensors):
                await asyncio.sleep(0)
            else:
                break
        
        await self.a_agent.send_message("action", "stop")

    async def run(self):
        self.state = self.STOPPED
        try:
            while True:
                if self.state == self.STOPPED:
                    # Ensure there are no obstacles in moving direction
                    while True:
                        front_sensors = []
                        for index, ray in enumerate(zip(*self.rc_sensor.sensor_rays)):
                            if -30 <= ray[Sensors.RayCastSensor.ANGLE] <= 30:
                                front_sensors.append(ray)
                        
                        if any(ray[Sensors.RayCastSensor.HIT] == 1 for ray in front_sensors):
                            await self.turn_until_clear()
                        else:
                            break
                    
                    # Start moving forward
                    await self.a_agent.send_message("action", "mf")
                    print("Starting movement...")

                    self.state = self.MOVING

                elif self.state == self.MOVING:

                    # Probability of turning randomly    
                    if random.random() < 0.01:
                        await self.a_agent.send_message("action", random.choice(["tl","tr"]))
                        await asyncio.sleep(0.5)
                        await self.a_agent.send_message("action", "nt")

                    while True:
                        front_sensors = []
                        for index, ray in enumerate(zip(*self.rc_sensor.sensor_rays)):
                            if -30 <= ray[Sensors.RayCastSensor.ANGLE] <= 30:
                                front_sensors.append(ray)
                    
                        if any(ray[Sensors.RayCastSensor.HIT] == 1 for ray in front_sensors):
                            break
                        else:
                            await asyncio.sleep(0)
                    
                    await self.a_agent.send_message("action", "stop")
                    self.state = self.AVOIDING
                
                elif self.state == self.AVOIDING:
                    
                    while True:
                        front_sensors = []
                        for index, ray in enumerate(zip(*self.rc_sensor.sensor_rays)):
                            if -30 <= ray[Sensors.RayCastSensor.ANGLE] <= 30:
                                front_sensors.append(ray)
                        
                        if any(ray[Sensors.RayCastSensor.HIT] == 1 for ray in front_sensors):
                            await self.turn_until_clear()
                        else:
                            break

                    await self.a_agent.send_message("action", "mf")
                    self.state = self.MOVING                        
        
        except asyncio.CancelledError:
            print("***** TASK Avoid CANCELLED")
            await self.a_agent.send_message("action", "stop")
            self.state = self.STOPPED


class ChaseAstronaut:
    FOLLOWING = 0
    MOVE_AWAY = 1

    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.threshold = 0.5
        self.current_turn = None

    async def run(self):
        self.state = self.FOLLOWING

        try:
            await self.a_agent.send_message("action", "mf")

            while True:

                if self.state == self.FOLLOWING:

                    found = False
                    sensor_obj_info = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]

                    for index, value in enumerate(sensor_obj_info):

                        if value and value["tag"] == "Astronaut":

                            found = True
                            angle = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.ANGLE][index]
                            distance = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.DISTANCE][index]

                            if distance < self.threshold:
                                await self.a_agent.send_message("action", "ntm")
                                self.state = self.MOVE_AWAY
                                break

                            
                            if angle > 10:
                                if self.current_turn != "tr":
                                    await self.a_agent.send_message("action", "tr")
                                    self.current_turn = "tr"

                            elif angle < -10:
                                if self.current_turn != "tl":
                                    await self.a_agent.send_message("action", "tl")
                                    self.current_turn = "tl"

                            else:
                                if self.current_turn is not None:
                                    await self.a_agent.send_message("action", "nt")
                                    self.current_turn = None

                            break

                    if not found:
                        await self.a_agent.send_message("action", "ntm")
                        return False

                    await asyncio.sleep(0.02)

                elif self.state == self.MOVE_AWAY:

                    await self.a_agent.send_message("action", "stop")

                    # Girar en dirección opuesta al astronauta
                    action = random.choice(["tl", "tr"])
                    await self.a_agent.send_message("action", action)
                    await asyncio.sleep(random.uniform(0.4, 1.0))
                    await self.a_agent.send_message("action", "nt")
                    
                    # Avanzar hasta estar suficientemente lejos
                    await self.a_agent.send_message("action", "mf")
                    min_distance = 3.0  # distancia mínima para alejarse
                    start_pos = dict(self.a_agent.i_state.position)
                    
                    while True:
                        current_dist = calculate_distance(start_pos, self.a_agent.i_state.position)
                        if current_dist >= min_distance:
                            break
                        # Si hay obstáculo delante, para y termina igualmente
                        hits = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.HIT]
                        if any(hits[i] for i in range(len(hits))):
                            break

                        await asyncio.sleep(0.2)
                    
                    await self.a_agent.send_message("action", "ntm")
                    return True

        except asyncio.CancelledError:
            await self.a_agent.send_message("action", "stop")




                    




