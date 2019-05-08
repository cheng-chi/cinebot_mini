import Pynamixel

hardware = Pynamixel.hardwares.USB2AX("/dev/ttyACM0", 1000000)

system = Pynamixel.System(Pynamixel.Bus(hardware))

servo_0 = system.add_device(Pynamixel.devices.MX28, 0)
servo_1 = system.add_device(Pynamixel.devices.MX28, 1)
servo_2 = system.add_device(Pynamixel.devices.MX28, 2)
servo_3 = system.add_device(Pynamixel.devices.AX12, 3)
servo_4 = system.add_device(Pynamixel.devices.AX12, 4)
servo_5 = system.add_device(Pynamixel.devices.XL320, 5)

hardware.flush()
servo_0.goal_position.write(0x0800)
servo_1.goal_position.write(0x0800)
servo_2.goal_position.write(0x0800)
servo_3.goal_position.write(0x0200)
servo_4.goal_position.write(0x0200)
servo_5.goal_position.write(0x0200)

hardware.flush()
servo_0.torque_enable.write(0x0000)
servo_1.torque_enable.write(0x0000)
servo_2.torque_enable.write(0x0000)
servo_3.torque_enable.write(0x0000)
servo_4.torque_enable.write(0x0000)
servo_5.torque_enable.write(0x0000)