import subprocess
import argparse
import os
import threading
import signal
import sys
import time

# Global variables to store the processes
vhost_process = None
dir_process = None
domain = None

def parse_redirect(output_file):
    global domain
    with open(output_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'Did not follow redirect to' in line:
                get_domain = line.split()[6]
                domain = get_domain.split('//')[1]
                command = f"echo '{ip} {domain}' | sudo tee -a /etc/hosts"
                subprocess.run(command, shell=True, check=True)

def parse_port_range(output_file):
    ports = []
    with open(output_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split('/')
            if len(parts) > 1 and parts[1].strip().startswith('tcp'):
                port = parts[0].strip()
                if port.isdigit() and int(port) <= 10000:
                    ports.append(port)
    return ports

def fuzz_vhosts(target, ports, wordlist):
    global vhost_process
    if not os.path.exists(wordlist):
        print(f"Error: Wordlist file '{wordlist}' does not exist.")
        return
    
    for port in ports:
        if port == '80':
            print("\n" + "="*40)
            print(f"Starting initial ffuf for vhosts on port {port}")
            print("="*40 + "\n")
            with open('vhost_ffuf_output.txt', 'w') as outfile:
                cmd = ['ffuf', '-w', f'{wordlist}:FUZZ', '-u', f'http://{target}/', '-H', f'Host: FUZZ.{target}']
                print("Running command: " + " ".join(cmd))
                vhost_process = subprocess.Popen(cmd, stdout=outfile, stderr=subprocess.PIPE)
                time.sleep(10)
                vhost_process.terminate()

            size = get_first_size('vhost_ffuf_output.txt')
            if size:
                print("\n" + "="*40)
                print(f"Restarting ffuf for vhosts on port {port} with size filter {size}")
                print("="*40 + "\n")
                with open('vhost_ffuf_filtered_output.txt', 'w') as outfile:
                    cmd = ['ffuf', '-w', f'{wordlist}:FUZZ', '-u', f'http://{target}/', '-H', f'Host: FUZZ.{target}', '-fs', size]
                    print("Running command: " + " ".join(cmd))
                    vhost_process = subprocess.Popen(cmd, stdout=outfile, stderr=subprocess.PIPE)
                    vhost_process.wait()

def get_first_size(output_file):
    with open(output_file, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) > 4:
                size = parts[4].strip(',')
                return size
    return None

def fuzz_directory(target, ports, wordlist):
    global dir_process
    if not os.path.exists(wordlist):
        print(f"Error: Wordlist file '{wordlist}' does not exist.")
        return
    
    for port in ports:
        if port == '80':
            print("\n" + "="*40)
            print(f"Starting ffuf for directories on port {port}")
            print("="*40 + "\n")
            with open('dir_ffuf_output.txt', 'w') as outfile:
                cmd = ['ffuf', '-w', f'{wordlist}:FUZZ', '-u', f'http://{target}/FUZZ']
                dir_process = subprocess.Popen(cmd, stdout=outfile, stderr=subprocess.PIPE)
                dir_process.wait()

def handle_interrupt(signal, frame):
    global vhost_process, dir_process
    print("\nCtrl+C detected! Terminating fuzzing processes...")
    if vhost_process:
        vhost_process.terminate()
    if dir_process:
        dir_process.terminate()
    print_results()
    sys.exit(0)

def print_results():
    print("\n" + "="*40)
    print("Vhost Fuzzing Results")
    print("="*40 + "\n")
    if os.path.exists('vhost_ffuf_filtered_output.txt'):
        with open('vhost_ffuf_filtered_output.txt', 'r') as f:
            print(f.read())
    
    print("\n" + "="*40)
    print("Directory Fuzzing Results")
    print("="*40 + "\n")
    if os.path.exists('dir_ffuf_output.txt'):
        with open('dir_ffuf_output.txt', 'r') as f:
            print(f.read())

# Create a single parser
parser = argparse.ArgumentParser(description="nmap scan script")

# Add the IP argument
parser.add_argument("--ip", '-ip', type=str, help="IP for nmap scan", required=True)

# Add the extra argument
parser.add_argument("--extra", '-extra', type=str, help="Extra options for nmap scan (default: -sV -sC -oN nmap_scan.txt)")

# Add the output argument
parser.add_argument("--output", '-output', type=str, help="Output file for nmap scan (default: nmap_scan.txt)")

# Add the wordlist argument
parser.add_argument("--wordlist", '-w', type=str, help="Wordlist file for directory fuzzing", required=True)

parser.add_argument("--vwordlist", '-vw', type=str, help="Wordlist file for vhost fuzzing", required=True)

# Parse the arguments
args = parser.parse_args()

# Get the IP, extra options, output file, and wordlist
ip = args.ip
extra = args.extra
output = args.output
wordlist = args.wordlist
vwordlist = args.vwordlist

# Set default value for output if not provided
if output is None:
    output = "nmap_scan.txt"

# Set default value for extra options if not provided
if extra is None:
    extra = "-sV -sC"

# Split the extra options into a list if they are provided as a single string
extra_options = extra.split()

print("="*40)
print("Starting nmap scan")
print("="*40 + "\n")

# Run the nmap scan with the provided options
subprocess.run(["nmap"] + extra_options + [ip, "-oN", output])
parse_redirect(output)

print("\n" + "="*40)
print("Nmap scan completed")
print("="*40 + "\n")

# Determine the target to use for fuzzing
target = domain if domain else ip

# Parse the port range from the output file
ports = parse_port_range(output)
print(f"Ports found: {ports}")

# Set up signal handler for Ctrl+C
signal.signal(signal.SIGINT, handle_interrupt)

# Create and start threads for fuzzing vhosts and directories
t1 = threading.Thread(target=fuzz_vhosts, args=(target, ports, vwordlist))
t2 = threading.Thread(target=fuzz_directory, args=(target, ports, wordlist))

t1.start()
t2.start()

t1.join()
t2.join()

print("\n" + "="*40)
print("Fuzzing completed")
print("="*40 + "\n")

print_results()
