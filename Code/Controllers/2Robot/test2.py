from controller import Robot

TIME_STEP = 64

class MyRobot(Robot):
    def __init__(self):
        super(MyRobot, self).__init__()
        self.left_motor = self.getDevice('Wheel1')
        self.right_motor = self.getDevice('Wheel2')
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)

    def run(self):
        while self.step(TIME_STEP) != -1:
            self.left_motor.setVelocity(SPEED)
            self.right_motor.setVelocity(SPEED)


            def use_accelerometer(self):
                accelerometer = self.getDevice('accelerometer')
                accelerometer.enable(TIME_STEP)
                
                while self.step(TIME_STEP) != -1:
                    values = accelerometer.getValues()
                    # Use the accelerometer values here
                    # Example: print(values)
                    print(values)
                    if values[0] > 0.5:
                        self.left_motor.setVelocity(SPEED)
                        self.right_motor.setVelocity(SPEED)
                    else:
                        self.left_motor.setVelocity(0.0)
                        self.right_motor.setVelocity(0.0)
                
                def calculate_position(acceleration, initial_velocity, initial_position, time):
                    velocity = initial_velocity + acceleration * time
                    position = initial_position + initial_velocity * time + 0.5 * acceleration * time**2
                    return position



if __name__ == "__main__":
    robot_instance = MyRobot()
    robot_instance.run()


