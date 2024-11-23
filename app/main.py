from flask import Flask, render_template, request
import subprocess
import docker

app = Flask(__name__, template_folder='../frontend')

# Disable session management
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = None

client = docker.from_env()

HOST_PID = 1  # Host PID (since we share PID namespace)

def run_on_host(cmd):
    nsenter_cmd = ['nsenter', '--target', str(HOST_PID), '--mount', '--uts', '--ipc', '--net', '--pid'] + cmd
    result = subprocess.run(nsenter_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    ip_a_output = ''
    lsusb_output = ''

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'shutdown':
            run_on_host(['shutdown', '-h', 'now'])
            message = 'Shutting down the host...'
        elif action == 'ip_a':
            container = client.containers.get('ubuntu_container')  # TODO we should add a name to ros2 container
            exec_result = container.exec_run('ip a')
            ip_a_output = exec_result.output.decode('utf-8')
        elif action == 'lsusb':
            result = run_on_host(['lsusb'])
            lsusb_output = result.stdout.decode('utf-8')

    return render_template('index.html',
                           message=message,
                           ip_a_output=ip_a_output,
                           lsusb_output=lsusb_output)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
