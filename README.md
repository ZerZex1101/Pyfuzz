# Pyfuzz

# FuzzMap

This script automates the process of performing an Nmap scan, detecting redirects, modifying the `/etc/hosts` file, and fuzzing for virtual hosts and directories using `ffuf`.

## Features

- Runs an Nmap scan with customizable options
- Detects HTTP redirects and updates the `/etc/hosts` file
- Fuzzes virtual hosts and directories on detected ports using `ffuf`
- Handles interrupts gracefully and displays results

## Requirements

- Python 3.x
- `ffuf` tool installed
- Sudo permissions to modify `/etc/hosts`

## Usage

usage: FuzzMap.py [-h] --ip IP [--extra EXTRA] [--output OUTPUT] --wordlist WORDLIST --vwordlist VWORDLIST

options:
  -h, --help            show this help message and exit
  --ip IP, -ip IP       IP for nmap scan
  --extra EXTRA, -extra EXTRA
                        Extra options for nmap scan (default: -sV -sC -oN nmap_scan.txt)
  --output OUTPUT, -output OUTPUT
                        Output file for nmap scan (default: nmap_scan.txt)
  --wordlist WORDLIST, -w WORDLIST
                        Wordlist file for directory fuzzing
  --vwordlist VWORDLIST, -vw VWORDLIST
                        Wordlist file for vhost fuzzing

Once the scan gets to vhost and directory fuzzing, there will be no output, but the scan will continue until you press Ctrl+C. At that point, the scan will stop, and the output will be shown.

## Example

python3 FuzzMap.py --ip 192.168.1.1 --wordlist dir_wordlist.txt --vwordlist vhost_wordlist.txt
