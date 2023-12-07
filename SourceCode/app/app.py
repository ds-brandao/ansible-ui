import streamlit as st
import subprocess
import re
import getpass
import os
import tempfile
import pandas as pd

# Define file paths
ansible_dir = '/etc/ansible/playbooks/'
hosts_file_path = '/etc/ansible/hosts'
playbooks = ['setStaticRoute.yaml', 'updateYum.yaml']  # Add additional playbooks
playbook_file_paths = [os.path.join(ansible_dir, playbook) for playbook in playbooks]
vault_password_file_path = "/usr/src/app/vaultPass.sh"

# Change the working directory to the Ansible playbooks directory
os.chdir(ansible_dir)

# Add a title
st.title('Run Ansible-Playbooks')
st.header("Upload a `.CSV` and run `playbook(s)`:")

def read_devices_from_file(file_path): 
    with open(file_path, 'r') as file:
        lines = file.readlines()
        devices = []
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('['):  # This is a group name
                    group_name = line.strip('[]')
                    devices.append('Group: ' + group_name)
                else:  # This is a hostname
                    hostname = line.split()[0]
                    devices.append(hostname)
        return devices

def read_lines_from_file(file_path): 
    with open(file_path, 'r') as file:
        lines = file.readlines()
        result_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('['):  # This is not a group label
                result_lines.append(line)
        return "\n".join(result_lines)

def handle_playbook_staticRoute(playbook_selection, deviceIPs):
    desired_staticRoutes = None
    if playbook_selection == 'setStaticRoute.yaml':
        st.markdown("---")    
        st.markdown("""
            For the selected playbook, you will need to upload a CSV file with the *desired static route* and the *device hostname* where the static route should be configured.
            The hosts name should be the same as the one defined in the Ansible hosts file. At `/etc/ansible/hosts`.
            The CSV file should have the following column labels:
            | staticRoute | deviceIP |
            |-------------|----------|
            - `staticRoute`: The static route.
            - `deviceIP`: The hostname of the device where the static route should be configured.
            """)
        desired_route_file = st.file_uploader('Upload a CSV file for the desired static route:', type=['csv'])
        error_occurred = False  
        if desired_route_file is not None:
            desired_route_df = pd.read_csv(desired_route_file)
            desired_staticRoutes = {}
            for index, row in desired_route_df.iterrows():
                device = row['deviceIP']
                if device not in deviceIPs:
                    st.error(f'Device with IP {device} does not exist in the hosts file.')
                    error_occurred = True  
                    break  
                else:
                    st.success(f'Device with IP {device} exists in the hosts file.')
                    desired_staticRoutes[device] = row['staticRoute']
    return desired_staticRoutes

def handle_playbook_updateYum(playbook_selection, devices):
    device_ip = None
    if playbook_selection == 'updateYum.yaml':
        # User selects the device from the dropdown
        device_ip = st.selectbox("Select a device:", devices)
        
        # Button to trigger the Ansible playbook
        if st.button("Run Playbook"):
            playbook_file_path = os.path.join(ansible_dir, playbook_selection)
            command = f"ansible-playbook -i {hosts_file_path} {playbook_file_path} --extra-vars \"device_selection={device_ip}\" --vault-password-file {vault_password_file_path}"
            
            try:
                process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
                output = process.stdout
                error = process.stderr

                # Display the output
                if process.returncode == 0:
                    st.success(f"Playbook ran successfully. Output: {output.decode('utf-8')}")
                    if error:
                        st.warning(f"Warning: {error.decode('utf-8')}")
                else:
                    st.error(f"Playbook failed. Error: {error.decode('utf-8')}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    return device_ip
 
def run_setStaticRoute_playbook(desired_staticRoutes):
    # Button to trigger the Ansible playbook
    if st.button("Run Playbook"):
        error_occurred = False  # Flag to indicate if an error occurred
        for static_route in desired_staticRoutes.values():
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', static_route):
                st.error(f'Invalid input: {static_route}. Please follow the format: 0.0.0.0 0.0.0.0 <next-hop>')
                error_occurred = True  # Set the flag to True
                break  # Stop the loop
            
        if not error_occurred:

            process = None
        try:
            for device_ip, static_route in desired_staticRoutes.items():
                # Check if device_ip is 'DLL'
                if device_ip == 'DLL':
                    playbook_file_path = '/etc/ansible/playbooks/updateYum.yaml'
                else:
                    playbook_file_path = os.path.join(ansible_dir, playbook_selection)

                command = f"ansible-playbook -i {hosts_file_path} {playbook_file_path} --extra-vars \"device_selection={device_ip} desired_route='{static_route}'\" --vault-password-file {vault_password_file_path}"
                process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
                output = process.stdout
                error = process.stderr

                # Display the output
                if process.returncode == 0:
                    st.success(f"Playbook ran successfully. Output: {output.decode('utf-8')}")
                    if error:
                        st.warning(f"Warning: {error.decode('utf-8')}")
                else:
                    st.error(f"Playbook failed. Error: {error.decode('utf-8')}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Read the devices from the hosts file
devices = read_devices_from_file(hosts_file_path) # Hostnames of the devices
deviceIPs = read_lines_from_file(hosts_file_path) #IP addresses of the devices

# User selects the device from the dropdown
#device_selection = st.selectbox("Select a device:", devices)

# User selects the playbook from the dropdown
playbook_selection = st.selectbox("Select a playbook:", playbooks)
playbook_file_path = os.path.join(ansible_dir, playbook_selection)

if playbook_selection == 'setStaticRoute.yaml':
    # Call the function to handle the staticRoute playbook
    desired_staticRoutes = handle_playbook_staticRoute(playbook_selection, deviceIPs)
    # Call the Button function
    run_setStaticRoute_playbook(desired_staticRoutes)
elif playbook_selection == 'updateYum.yaml':
    # Call the function to handle the updateYum playbook
    handle_playbook_updateYum(playbook_selection, devices)


#print (desired_staticRoutes)

# Call the Button function
#run_setStaticRoute_playbook(desired_staticRoutes)

# Add a horizontal line
st.markdown("---")

