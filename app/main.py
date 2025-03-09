from flask import Flask, render_template, request
import subprocess
import docker
import base64
from time import sleep
from grab_camera import decode_to_jpg

# app = Flask(__name__, template_folder='../frontend')
app = Flask(__name__, template_folder='./frontend')

# Disable session management
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = None

client = docker.from_env()

HOST_PID = 1  # Host PID (since we share PID namespace)

def run_on_host(cmd):
    nsenter_cmd = ['nsenter', '--target', str(HOST_PID), '--mount', '--uts', '--ipc', '--net', '--pid'] + cmd
    result = subprocess.run(nsenter_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result

def run_in_container_then_stop(container, start_cmd, stop_cmd, duration):
    container.exec_run(start_cmd)
    sleep(duration)
    container.exec_run(stop_cmd)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    container_output = ''
    host_output = ''
    image_data_bottom = None
    image_data_front = None

    if request.method == 'POST':
        container = client.containers.get('ubc_subbots')
        action = request.form.get('action')

        # thruster testing
        if "thruster1" in action:
            run_in_container_then_stop(container, 
                """bash -c 'source /ros_entrypoint.sh && source ~/triton/install/setup.bash && timeout 5s ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000010001"'""",
                """bash -c 'source /ros_entrypoint.sh && source ~/triton/install/setup.bash && timeout 7s ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000010000"'""",
                1)
        elif "thruster2" in action:
            run_in_container_then_stop(container, 
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000110000"',
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000010000"',
                2)
        elif "thruster3" in action:
            run_in_container_then_stop(container, 
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100011000010000"',
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000010000"',
                2)
        elif "thruster4" in action:
            run_in_container_then_stop(container, 
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010001100001000010000"',
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000010000"',
                2)
        elif "thruster5" in action:
            run_in_container_then_stop(container, 
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000110000100001000010000"',
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000010000"',
                2)
        elif "thruster6" in action:
            run_in_container_then_stop(container, 
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100011000010000100001000010000"',
                'ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000010000"',
                2)


        # movements
        elif "move-front" in action:
            run_in_container_then_stop(container, 
                """bash -c 'source /ros_entrypoint.sh && source ~/triton/install/setup.bash && timeout 5s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 15.0, y: 0, z: 0}}"'""",
                """bash -c 'source /ros_entrypoint.sh && source ~/triton/install/setup.bash && timeout 5s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: 0}}"'""",
                1)
        elif "move-back" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: -15.0, y: 0, z: 0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: 0, z: 0}}'",
                2)
        elif "move-left" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: 15.0, z: 0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: 0, z: 0}}'",
                2)
        elif "move-right" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: -15.0, z: 0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: 0, z: 0}}'",
                2)
        elif "move-up" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: 0, z: 15.0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: 0, z: 0}}'",
                2)
        elif "move-down" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: 0, z: -15.0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/Wrench '{force: {x: 0, y: 0, z: 0}}'",
                2)
        elif "move-ccw" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/torque '{force: {x: 0, y: 0, z: 15.0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/torque '{force: {x: 0, y: 0, z: 0}}'",
                2)
        elif "move-cw" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/torque '{force: {x: 0, y: 0, z: -15.0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/torque '{force: {x: 0, y: 0, z: 0}}'",
                2)
        elif "move-tilt-left" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/torque '{force: {x: -15.0, y: 0, z: 0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/torque '{force: {x: 0, y: 0, z: 0}}'",
                2)
        elif "move-tilt-right" in action:
            run_in_container_then_stop(container, 
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/torque '{force: {x: 15.0, y: 0, z: 0}}'",
                "ros2 topic pub /triton/control/input_forces geometry_msgs/msg/torque '{force: {x: 0, y: 0, z: 0}}'",
                2)

        # Camera and Sensors
        elif action == 'camera-bottom-update':
            # TODO source commands would output something causing the actual image data to not be picked up
            bottom_output = container.exec_run('bash -c "source /ros_entrypoint.sh && source ~/triton/install/setup.bash && timeout 15s ros2 topic echo /triton/drivers/bottom_camera/image_raw -f --csv"')
            if len(bottom_output) > 1:
                raw_camera_bottom_csv = bottom_output.output.decode(encoding="utf-8").split('\n',1)[0]
                jpg_raw = decode_to_jpg(raw_camera_bottom_csv)
                if jpg_raw:
                    image_data_bottom = f"data:image/jpeg;base64,{base64.b64encode(jpg_raw).decode('utf-8')}"
                    container_output = "Bottom Camera Updated Successfully"
                else:
                    container_output = "Failed to grab bottom camera image, no convert output"
            else:
                container_output = "Failed to grab bottom camera image, no data"

        elif action == 'camera-front-update':
            front_output = container.exec_run('bash -c "source /ros_entrypoint.sh && source ~/triton/install/setup.bash && timeout 15s ros2 topic echo /triton/drivers/front_camera/image_raw -f --csv"')
            if len(front_output) > 1:
                raw_camera_front_csv = front_output.output.decode(encoding="utf-8").split('\n',1)[0]
                jpg_raw = decode_to_jpg(raw_camera_front_csv)
                if jpg_raw:
                    image_data_front = f"data:image/jpeg;base64,{base64.b64encode(jpg_raw).decode('utf-8')}"
                    container_output = "Front Camera Updated Successfully"
                else:
                    container_output = "Failed to grab front camera image, no convert output"
            else:
                container_output = "Failed to grab front camera image, no data"


        # Dangerous Zone
        elif action == 'shutdown':
            run_on_host(['shutdown', '-h', 'now'])
            message = 'Shutting down the host...'
        elif action == 'reboot':
            run_on_host(['shutdown', '-r', 'now'])
            message = 'Rebooting the host...'
        elif action == 'ip_a':
            exec_result = container.exec_run('ifcomfig')
            container_output = exec_result.output.decode('utf-8')
        elif action == 'lsusb':
            result = run_on_host(['lsusb'])
            host_output = result.stdout.decode('utf-8')

    return render_template('index.html',
                           message=message,
                           container_output=container_output,
                           host_output=host_output,
                           image_data_bottom=image_data_bottom)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
