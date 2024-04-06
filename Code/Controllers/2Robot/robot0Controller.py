from controller import Robot

# Define the time step and the speed variable
TIME_STEP = 64
SPEED = 6.0  # You can change this value to adjust the robot's speed

class MyRobot(Robot):
    def __init__(self):
        super(MyRobot, self).__init__()
        # Initialize motors with the custom names provided
        self.left_motor = self.getDevice('Wheel1')
        self.right_motor = self.getDevice('Wheel2')
        self.left_motor.setPosition(float('inf'))  # Velocity control mode
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0.0)  # Initial speed
        self.right_motor.setVelocity(0.0)

    def run(self):
        while self.step(TIME_STEP) != -1:
            # Set both wheels to the same speed to move forward
            self.left_motor.setVelocity(SPEED)
            self.right_motor.setVelocity(SPEED)
            # Here, you can integrate additional logic for sensor data processing and decision making

if __name__ == "__main__":
    robot_instance = MyRobot()
    robot_instance.run()


