from flask import Flask, render_template, request
import subprocess
import docker
import base64
import time
import select
from time import sleep
from grab_camera import decode_to_jpg

# app = Flask(__name__, template_folder='../frontend')
app = Flask(__name__, template_folder='./frontend')

# Disable session management
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = None

client = docker.from_env()

HOST_PID = 1  # Host PID (since we share PID namespace)

container = None
sock = None

exec_output = ''

def initial_setup():
    container = client.containers.get('steelhead_thrusters')
    exec_result = container.exec_run(
        cmd="bash --rcfile ~/.bashrc -i",
        tty=True,
        stdin=True,
        socket=True
    )

    sock = exec_result.output._sock

def run_on_host(cmd):
    nsenter_cmd = ['nsenter', '--target', str(HOST_PID), '--mount', '--uts', '--ipc', '--net', '--pid'] + cmd
    result = subprocess.run(nsenter_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result

def run_in_container(cmd):
    sock.sendall(command.encode('utf-8') + b'\n')

def run_in_container_then_stop(container, start_cmd, stop_cmd, start_timeout, stop_timeout):
    run_in_container(start_cmd)
    sleep(start_timeout)
    run_in_container(stop_cmd)
    sleep(stop_timeout)
    return read_output()

def read_output(timeout = 1.0):
    start_time = time.time()
    output = b""
    
    while True:
        # If we exceed the timeout, break
        if time.time() - start_time > timeout:
            break
        
        # Check if the socket is readable
        r, w, e = select.select([sock], [], [], 0.1)
        
        # If it's readable, recv() the data
        if sock in r:
            chunk = sock.recv(4096)
            if not chunk:
                # No more data, or the shell might have closed
                break
            output += chunk
        else:
            # No data ready yet, short break
            break
    
    return output.decode('utf-8', errors='replace')

def thruster_calculator(force):
    if not -16 <= n <= 15:
        return '00000'

    sign_bit = '0' if n >= 0 else '1'
    magnitude = abs(n)
    magnitude_bits = f"{magnitude:04b}"  # 4 bits for magnitude
    return sign_bit + magnitude_bits

# changed to interactive shell https://chatgpt.com/share/67cd36b4-1c84-800d-86a6-c04ab10facf7
# TODO add a button to initialize everything (run container, start launch files etc)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    image_data_bottom = None
    image_data_front = None

    if request.method == 'POST':
        action = request.form.get('action')

        # thruster testing
        if "test-thrusters" in action:
            thruster1 = request.form['thruster1_value']
            thruster2 = request.form['thruster2_value']
            thruster3 = request.form['thruster3_value']
            thruster4 = request.form['thruster4_value']
            thruster5 = request.form['thruster5_value']
            thruster6 = request.form['thruster6_value']
            runtime   = request.form['time_seconds'] + 2

            thruster_powers = thruster_calculator(thruster6) + thruster_calculator(thruster5) + thruster_calculator(thruster4) + thruster_calculator(thruster3) + thruster_calculator(thruster2) + thruster_calculator(thruster1)

            thruster_command = 'timeout ' + runtime + 's ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00' + thruster_powers + '"'

            exec_output += run_in_container_then_stop(container, thruster_command, 'timeout 3s ros2 topic pub /motor_control std_msgs/msg/UInt32 "data: 0b00100001000010000100001000010000"', runtime, 4)

        # movements
        elif "move-front" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 15.0, y: 0, z: 0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-back" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: -15.0, y: 0, z: 0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-left" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 15.0, z: 0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-right" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: -15.0, z: 0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-up" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: 15.0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-down" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: -15.0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/Wrench "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-ccw" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/torque "{force: {x: 0, y: 0, z: 15.0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/torque "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-cw" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/torque "{force: {x: 0, y: 0, z: -15.0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/torque "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-tilt-left" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/torque "{force: {x: -15.0, y: 0, z: 0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/torque "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)
        elif "move-tilt-right" in action:
            exec_output += run_in_container_then_stop(container, 
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/torque "{force: {x: 15.0, y: 0, z: 0}}"',
                'timeout 4s ros2 topic pub /triton/controls/input_forces geometry_msgs/msg/torque "{force: {x: 0, y: 0, z: 0}}"',
                4, 4)

        # Camera and Sensors
        elif action == 'camera-bottom-update':
            read_output()
            # TODO source commands would output something causing the actual image data to not be picked up
            run_in_container('timeout 8s ros2 topic echo /triton/drivers/bottom_camera/image_raw -f --csv')
            sleep(8500)
            bottom_output = read_output()
            bottom_output.split('\r\n')
            if len(bottom_output) > 2:
                raw_camera_bottom_csv = bottom_output[3]
                jpg_raw = decode_to_jpg(raw_camera_bottom_csv)
                if jpg_raw:
                    image_data_bottom = f"data:image/jpeg;base64,{base64.b64encode(jpg_raw).decode('utf-8')}"
                    exec_output = "Bottom Camera Updated Successfully"
                else:
                    exec_output = "Failed to grab bottom camera image, no convert output"
            else:
                exec_output = "Failed to grab bottom camera image, no data"

        elif action == 'camera-front-update':
            read_output()
            front_output = run_in_container('timeout 8s ros2 topic echo /triton/drivers/front_camera/image_raw -f --csv')
            sleep(8500)
            front_output = read_output()
            front_output.split('\r\n')
            if len(front_output) > 2:
                raw_camera_bottom_csv = front_output[3]
                jpg_raw = decode_to_jpg(raw_camera_front_csv)
                if jpg_raw:
                    image_data_front = f"data:image/jpeg;base64,{base64.b64encode(jpg_raw).decode('utf-8')}"
                    exec_output = "Front Camera Updated Successfully"
                else:
                    exec_output = "Failed to grab front camera image, no convert output"
            else:
                exec_output = "Failed to grab front camera image, no data"


        # Dangerous Zone
        elif action == 'shutdown':
            run_on_host(['shutdown', '-h', 'now'])
            message = 'Shutting down the host...'
        elif action == 'reboot':
            run_on_host(['shutdown', '-r', 'now'])
            message = 'Rebooting the host...'
        elif action == 'ip_a':
            exec_result = container.exec_run('ifconfig')
            exec_output = exec_result.output.decode('utf-8')
        elif action == 'lsusb':
            result = run_on_host(['lsusb'])
            exec_output = result.stdout.decode('utf-8')

    return render_template('index.html',
                           message=message,
                           exec_output=exec_output,
                           image_data_bottom=image_data_bottom)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
