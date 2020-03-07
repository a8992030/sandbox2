# Installation
### [MAC OS]
1. Install XQuartz
2. In the XQuartz preferences, go to the “Security” tab and make sure you’ve got “Allow connections from network clients” ticked
3. Reboot MacOS

# Before Executing ./docker.tool
### [MAC OS]

####Add an alias IP 172.16.123.1 to the loopback adapter

`sudo ifconfig lo0 alias 172.16.123.1 `

####Remove it
`sudo ifconfig lo0 -alias 172.16.123.1`

