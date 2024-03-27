#Sourced from: https://cyberbotics.com/doc/guide/using-distance-sensors
#Tutorial:https://www.youtube.com/watch?v=stighxiYKlo&t=1137s
from controller import Robot

timeStep = 32
maxSpeed = 6.28

robot = Robot()

wheel_left = robot.getMotor("left wheel motor")
wheel_right = robot.getMotor("right wheel motor")

leftSensors = []
rightSensors = []
frontSensors = []

frontSensors.append(robot.getDistanceSensor("ps7"))
frontSensors[0].enable(timeStep)
frontSensors.append(robot.getDistanceSensor("ps0"))
frontSensors[1].enable(timeStep)

rightSensors.append(robot.getDistanceSensor("ps1"))
rightSensors[0].enable(timeStep)
rightSensors.append(robot.getDistanceSensor("ps2"))
rightSensors[1].enable(timeStep)

leftSensors.append(robot.getDistanceSensor("ps5"))
leftSensors[0].enable(timeStep)
leftSensors.append(robot.getDistanceSensor("ps6"))
leftSensors[1].enable(timeStep)

# [left, right]
speeds = [max_velocity, max_velocity]

wheel_left.setPosition(float("inf"))
wheel_right.setPosition(float("inf"))

def turn_right():
    speeds[0] = 0.6 * max_velocity
    speeds[1] = -0.2 * max_velocity

def turn_left():
    speeds[0] = -0.2 * max_velocity
    speeds[1] = 0.6 * max_velocity

def spin():
    speeds[0] = 0.6 * max_velocity
    speeds[1] = -0.6 * max_velocity


while robot.step(timeStep) != -1:
    speeds[0] = max_velocity
    speeds[1] = max_velocity  

    for i in range(2):
        if leftSensors[i].getValue() < 80.0: #levi
            turn_right()
        elif rightSensors[i].getValue() < 80.0: #desni
            turn_left()
    
    if frontSensors[0].getValue() < 80.0 or frontSensors[1].getValue() < 80.0:
        spin()
