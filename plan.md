this is a python project, the goal is to create a cloud native database driven simulation tools using QEMU and SQLITE.

Request service is to allow user register their request into a table of the sqlite database, specifying the parameters
1. the virtual machine name, 
2. commands to run after the virtual machine is booted
3. optionally timeout in second (system default 5 seconds)
the table should also hold a few metadata for the request such as
1. date and time of the request is recevied
2. UUID as a user request unique identifier
request log linked to the UUID
3. request status (pending, acknowledged, running, cancelled, hold, done)
4. data and time of the last update

One or more instances of agent service monitors the request table in the sqlite database, once there is a new request is registered, a work log table is created to record the job performed
1. create a new table based name of the user request's UUID if it does not exist
2. launch a qemu bash script based on the virtual machine name user requested
3. record output from stdio to table every 1 second and the actual date and time
4. when the kernel is boot
5. send user requested command to target
6. record output from stdio to table every 1 second and the actual date and time
7. terminate qemu if there is no output exceed the timeout period

create a tools in python for user to enquire the request and inspect work log
