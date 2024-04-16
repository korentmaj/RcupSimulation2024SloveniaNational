from controller import Robot, Camera, Motor, PositionSensor
import cv2
import numpy as np

# Create robot object
robot = Robot()
timeStep = int(robot.getBasicTimeStep())

# Camera setup
camera = robot.getDevice("camera1")
camera.enable(timeStep)

# Motor setup
wheel_left = robot.getDevice("wheel1")
wheel_right = robot.getDevice("wheel2")
wheel_left.setPosition(float('inf'))  # Set to infinite position mode
wheel_right.setPosition(float('inf'))

leftEncoder = wheel_left.getPositionSensor()
rightEncoder = wheel_right.getPositionSensor()
leftEncoder.enable(timeStep)
rightEncoder.enable(timeStep)

wheel_left.setVelocity(5.0)  # Set initial velocity
wheel_right.setVelocity(5.0)

# Main robot loop
while robot.step(timeStep) != -1:
    # Handle the camera image
    image = camera.getImage()
    image = np.frombuffer(image, np.uint8).reshape((camera.getHeight(), camera.getWidth(), 4))
    frame = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    cv2.imshow("frame", frame)

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Grayscale conversion
    cv2.imshow("grayScale", frame)

    _, thresh = cv2.threshold(frame, 80, 255, cv2.THRESH_BINARY)  # Apply threshold
    cv2.imshow("thresh", thresh)

    cv2.waitKey(1)  # Render imshow frames on screen

    # Check the encoder value to stop the robot after some movement
    if leftEncoder.getValue() > 20.0:   # If left motor has spun more than 20 radians
        wheel_left.setVelocity(0.0)
        wheel_right.setVelocity(0.0)
        break


