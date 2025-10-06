#COMPANY CLIENT 01: 

#######################################################################################
# TODO: You can find your group number on CANVAS, eg, if you are group 3, then put "03"
group_number = "00"
#######################################################################################

# import all the required libraries
from opcua import Client
from time import sleep
import numpy as np
import threading
from datetime import datetime
import sys

######################################################################################
# Assign endpoint URL
# Make sure url is same as server url
# TODO: assign correct url and port for client code
url = "localhost"
port = 7001

# Assemble endpoint url
# TODO: assemble the endpoint
end_point = f"opc.tcp://{url}:{port}"
######################################################################################

try:
    # Assign endpoint url on the OPC UA client  address space
    client = Client(end_point)

    # Load list of operation request sent by client 1
    Company_1_operation_list = np.loadtxt("Company_1_Operation_List.txt", dtype='str', delimiter=',')

    # Create file instance for client 1 progress file
    Client1_progress_file = open("Group_{}_Progress_Client_1.txt".format(group_number), "w")

    # Create file instance for client 1 Machine Status file
    Client1_Machine_status_file = open("Group_{}_Machine_Status_Client_1.txt".format(group_number), "w")

    # Connect to server
    client.connect()
    # log data
    with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
        ctime = str(datetime.now().time())[:-7]
        f.write("{} - Connecting to OPC UA server \"{}\"\n".format(ctime, end_point))
    print("{} - Connecting to OPC UA server: \"{}\"".format(ctime, end_point))
    sleep(2)
except:
    print("!!!ERROR!!! Please initialise your OPC UA server code first!")
    sys.exit()

# Get the root node of the adress space
objects_node = client.get_objects_node()

# Get the children node of the objects Method
method = objects_node.get_children()

# Assign nodes (same mapping as Company 1)
"""
Explanation:
ns=0 → Standard OPC UA system nodes (built-in types, standard services)
ns=1 → Server vendor’s own namespace
ns=2 → Your custom namespace (the one you define in code)
Ex: 
Server code line	Variable name	Created with add_variable(idx, ...)	NodeId assigned
76	Equipment_ID1 = “Conveyor”	1st custom variable	ns=2;i=2
77	Equipment_ID2 = “KUKA”	2nd variable	ns=2;i=3
78	Equipment_ID3 = “Lathe”	3rd variable	ns=2;i=4

"""

##################################################################################################
# Assign nodes (namespace 2 is where the server registered the assignment namespace)
# Mapping follows the order of add_variable(...) in the server.
Equipment_ID1 = client.get_node("ns=2;i=2")   # Example (Conveyor)
Equipment_ID2 = client.get_node("ns=2;i=3")   # KUKA
Equipment_ID3 = client.get_node("ns=2;i=4")   # Lathe

time_left_conveyor = client.get_node("ns=2;i=5")  # remaining_con
time_left_kuka     = client.get_node("ns=2;i=6")  # remaining_Kuka
time_left_Lathe    = client.get_node("ns=2;i=7")  # remaining_Lathe

current_time = client.get_node("ns=2;i=9")        # Time Stamp

Kuka_operation  = client.get_node("ns=2;i=10")    # KUKA Current Operation
Lathe_operation = client.get_node("ns=2;i=11")    # Lathe Current Operation

WorkpieceID = client.get_node("ns=2;i=12")        # WorkpieceID

Conveyor_Status = client.get_node("ns=2;i=13")    # Status_con
Kuka_Status     = client.get_node("ns=2;i=14")    # Status_Kuka
Lathe_Status    = client.get_node("ns=2;i=15")    # Status_Lathe
###################################################################################################

# Flag of switching status
Client1_Machine_status_flag = True
Operation_completion_flag = False

# log data
with open("Group_{}_Machine_Status_Client_1.txt".format(group_number), "a") as f:
    f.write(
        "{:<10}|{:<20}|{:<20}|{:<20}|{:<20}|{:<20}|{:<20}\n".format("Time", "Conveyor Belt", "KUKA Robot", "CNC Lathe",
                                                                    "Workpiece ID", "KUKA Operation",
                                                                    "CNC Lathe Operation"))
    f.write(
        "{:<10}|{:<10}|{:<9}|{:<10}|{:<9}|{:<10}|{:<9}\n".format(" ", "Status", "R_Time", "Status", "R_Time",
                                                                 "Status", "R_Time", )
    )

# function of multithreading logging operation
def Record_machine_status():
    while Client1_Machine_status_flag:

        global Workpiece
        global Current_Operation_log

        Workpiece = WorkpieceID.get_value()

        with open("Group_{}_Machine_Status_Client_1.txt".format(group_number), "a") as f:
            f.write(
                "{:<10}|{:<10}|{:<9}|{:<10}|{:<9}|{:<10}|{:<9}|{:<20}|{:<20}|{:<20}\n".format(current_time.get_value(),
                                                                                              Conveyor_Status.get_value(),
                                                                                              str(time_left_conveyor.get_value())+'s',
                                                                                              Kuka_Status.get_value(),
                                                                                              str(time_left_kuka.get_value()) + 's',
                                                                                              Lathe_Status.get_value(),
                                                                                              str(time_left_Lathe.get_value()) + 's',
                                                                                              Workpiece,
                                                                                              Kuka_operation.get_value(),
                                                                                              Lathe_operation.get_value())
            )

        if Operation_completion_flag:  # Condition to close the operation
            with open("Group_{}_Machine_Status_Client_1.txt".format(group_number), "a") as f:
                f.write("{} Completed!\n".format(Current_Operation_log))
                f.write("-" * 130 + "\n")

        sleep(1)


"""
Explanation:
In OPC UA, every server exposes a standard Address Space with well-known root folders. 
One of those is the Objects folder — it’s the entry point where servers put live “things” (instances, variables, and callable methods) that clients interact with.
Objects folder = a standard node (NodeId ns=0;i=85) that contains:built-in Server object,
any custom objects/folders your server creates (e.g., a parameters folder),
callable Method nodes (like Conveyor, Lathe_Prog1, etc.).
In your server, the first two children are objects (Server, parameters), and the rest are your methods.
That’s why Conveyor is at children[2].
Index	Node Type	BrowseName	Purpose
method[0]	Object	Server	Built-in system object (standard)
method[1]	Object	parameters	Your custom folder holding all variables (Equipment_ID, Status_…, etc.)
method[2]	Method	Conveyor	First callable method you added
method[3]	Method	Lathe_Prog1	Second callable method
method[4]	Method	Lathe_Prog2	Third callable method
method[5]	Method	Kuka_Prog1	Fourth callable method
method[6]	Method	Kuka_Prog2	Fifth callable method
"""


#############################################################################################
# Assigning method node ID to the variable
# Objects children ordering: ["Server", "parameters", "Conveyor", "Lathe_Prog1", "Lathe_Prog2", "Kuka_Prog1", "Kuka_Prog2"]
Start_Conveyor_prog = method[2]  # Example
Start_Lathe_Prog1   = method[3]
Start_Lathe_Prog2   = method[4]
Start_Kuka_Prog1    = method[5]
#############################################################################################

# Adding and starting a new thread
Add_new_thread = threading.Thread(target=Record_machine_status)
Add_new_thread.start()

# data log
with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
    ctime = str(datetime.now().time())[:-7]
    f.write("{} - Loading operation list\n".format(ctime))
    print("{} - Loading operation list".format(ctime))
    print("There are {} operations from Company 1".format(len(Company_1_operation_list)))
    f.write("There are {} Requests in the Operation List\n".format(len(Company_1_operation_list)))

# Loops for Initiating company's operation list
index = 1
for Current_operation in Company_1_operation_list:

    Operation_completion_flag = False  # Set to true when operation is completed

    # Conveyor and Kuka status check
    while Conveyor_Status.get_value() != "Idle    " or Kuka_Status.get_value() != "Idle    ":
        sleep(1.1)

    # data log
    print("-" * 30 + "OPERATION ({})".format(index) + "-" * 30)
    print("Starting {}".format(Current_operation))
    with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
        f.write("-" * 65 + "\n")
        f.write("Starting {}\n".format(Current_operation))

    # Assigning workpiece data and calling Start_Conveyor_prog on server program
    global Workpiece

    #############################################################################################
    # TODO: add code to link conveyor program start method and pass the current operation detail
    Workpiece = objects_node.call_method(Start_Conveyor_prog, Current_operation)
    #############################################################################################

    print("{} - Initialising Conveyor Belt".format(current_time.get_value()))

    # data log
    with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
        f.write("{} - Transferring a New Workpiece with ID: {}\n".format(current_time.get_value(), Workpiece))

    # Waiting for conveyor operation to complete
    while time_left_conveyor.get_value() != 0 and Conveyor_Status.get_value() != "Idle    ":
        pass

    # data log
    with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
        f.write("{} - Connecting to KUKA robot\n".format(current_time.get_value()))

    # Conditional loop for different operation
    if Current_operation == "Operation A":  # Operation A

        print("{} - Arriving the Destination on Conveyor Belt".format(current_time.get_value()))

        # Data log
        print("{} - Starting Kuka Robot Operation ---> Pick & Place Started".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - Starting Kuka Robot Operation ---> Pick & Place Started\n".format(current_time.get_value()))

        #############################################################################################
        # starting Start_Kuka_Prog1 program on kuka
        # TODO: add code to link Start_Kuka_Prog1 program  start method
        return_value_kuka_prog1 = objects_node.call_method(Start_Kuka_Prog1)
        #############################################################################################

        sleep(1)

        # Waiting for kuka operation to complete
        while time_left_kuka.get_value() != 0 and Kuka_Status.get_value() != "Idle    ":
            pass

        # data log
        print("{} - KUKA Operation Pick & Place Completed".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - KUKA Operation Pick & Place Completed\n".format(current_time.get_value()))
        sleep(0.5)

        print("{} - Opening CNC Lathe Door".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - Opening CNC Lathe Door\n".format(current_time.get_value()))
        sleep(1)

        print("{} - Closing CNC Lathe Door".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - Closing CNC Lathe Door\n".format(current_time.get_value()))
        sleep(1)

        print("{} - Starting Lathe Operation ---> Turning & Drilling".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - Starting Lathe Operation ---> Turning & Drilling\n".format(current_time.get_value()))
        sleep(1)

        #############################################################################################
        # starting Start_Lathe_Prog1 program on Lathe (Turning & Drilling)
        # TODO: add code to link Start_Lathe_Prog1 program start method
        return_value_lathe_prog1 = objects_node.call_method(Start_Lathe_Prog1)
        #############################################################################################

        sleep(0.1)

        # Waiting for lathe operation to complete
        while time_left_Lathe.get_value() != 0 and Lathe_Status.get_value() != "Idle    ":
            pass

    elif Current_operation == "Operation B":

        print("{} - Arriving the Destination on Conveyor Belt".format(current_time.get_value()))

        # data log
        print("{} - Starting Kuka Robot Operation ---> Pick & Place Started".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - Starting Kuka Robot Operation ---> Pick & Place Started\n".format(current_time.get_value()))

        #############################################################################################
        # starting Start_Kuka_Prog1 program on kuka
        # TODO: add code to link Start_Kuka_Prog1 program  start method
        return_value_kuka_prog1 = objects_node.call_method(Start_Kuka_Prog1)
        #############################################################################################

        sleep(1)

        # Waiting for kuka operation to complete
        while time_left_kuka.get_value() != 0 and Kuka_Status.get_value() != "Idle    ":
            pass

        # data log
        print("{} - KUKA Operation Pick & Place Completed".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - KUKA Operation Pick & Place Completed\n".format(current_time.get_value()))
        sleep(0.5)

        print("{} - Opening CNC Lathe Door".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - Opening CNC Lathe Door\n".format(current_time.get_value()))
        sleep(3)

        print("{} - Closing CNC Lathe Door".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - Closing CNC Lathe Door\n".format(current_time.get_value()))
        sleep(1)

        print("{} - Starting Lathe Operation ---> Turning & Threading".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
            f.write("{} - Starting Lathe Operation ---> Turning & Threading\n".format(current_time.get_value()))
        sleep(1)

        # starting Start_Lathe_Prog2 program on Lathe (Threading)
        return_value_lathe_prog2 = objects_node.call_method(Start_Lathe_Prog2)

        sleep(0.1)

        # Waiting for lathe operation to complete
        while time_left_Lathe.get_value() != 0 and Lathe_Status.get_value() != "Idle    ":
            pass

    else:  # invalid operation
        print("!!!ERROR!!! Invalid operation included!\n")
        sys.exit()

    ctime = str(datetime.now().time())[:-7]
    print("{} - {} Completed ".format(ctime, Current_operation))
    index += 1
    with open("Group_{}_Progress_Client_1.txt".format(group_number), "a") as f:
        f.write("{} - {} Completed\n".format(ctime, Current_operation))

    # Storing current operation information in a variable
    global Current_Operation_log
    Current_Operation_log = Current_operation

    # Assigning completion flag
    Operation_completion_flag = True

    sleep(1.1)

# status flag
Client1_Machine_status_flag = False



#COMPANY CLIENT 02:

# README
#
# This is the source code for the client assignment.
#
# Read through the (commented) code and try to understand it.

#######################################################################################
# TODO: You can find your group number on CANVAS, eg, if you are group 3, then put "03"
group_number = "00"
#######################################################################################

# import all the required libraries
from opcua import Client
from time import sleep
import numpy as np
import threading
from datetime import datetime
import sys

######################################################################################
# Assign endpoint URL
# Make sure url is same as server url
# TODO: assign correct url and port for client code
url = "localhost"
port = 7001

# Assemble endpoint url
# TODO: assemble the endpoint
end_point = f"opc.tcp://{url}:{port}"
######################################################################################

try:
    # Assign endpoint url on the OPC UA client  address space
    client = Client(end_point)

    # Load list of operation request sent by client 2
    Company_2_operation_list = np.loadtxt("Company_2_Operation_List.txt", dtype='str', delimiter=',')

    # Create file instance for client 2 progress file
    Client2_progress_file = open("Group_{}_Progress_Client_2.txt".format(group_number), "w")

    # Create file instance for client 2 Machine Status file
    Client1_Machine_status_file = open("Group_{}_Machine_Status_Client_2.txt".format(group_number), "w")

    # Connect to server
    client.connect()

    # log data
    with open("Group_{}_Progress_Client_2.txt".format(group_number), "a") as f:
        ctime = str(datetime.now().time())[:-7]
        f.write("{} - Connecting to OPC UA server \"{}\"\n".format(ctime, end_point))
    print("{} - Connecting to OPC UA server: \"{}\"".format(ctime, end_point))
    sleep(2)
except:
    print("!!!ERROR!!! Please initialise your OPC UA server code first!")
    sys.exit()

# Get the root node of the adress space
objects_node = client.get_objects_node()

# Get the children node of the objects Method
method = objects_node.get_children()

##################################################################################################
# Assign nodes (same mapping as Company 1)
"""
Explanation:
ns=0 → Standard OPC UA system nodes (built-in types, standard services)
ns=1 → Server vendor’s own namespace
ns=2 → Your custom namespace (the one you define in code)
Ex: 
Server code line	Variable name	Created with add_variable(idx, ...)	NodeId assigned
76	Equipment_ID1 = “Conveyor”	1st custom variable	ns=2;i=2
77	Equipment_ID2 = “KUKA”	2nd variable	ns=2;i=3
78	Equipment_ID3 = “Lathe”	3rd variable	ns=2;i=4

"""
Equipment_ID1 = client.get_node("ns=2;i=2")
Equipment_ID2 = client.get_node("ns=2;i=3")
Equipment_ID3 = client.get_node("ns=2;i=4")

time_left_conveyor = client.get_node("ns=2;i=5")
time_left_kuka     = client.get_node("ns=2;i=6")
time_left_Lathe    = client.get_node("ns=2;i=7")

# ns=2; i=8 is set for messaging:
current_time = client.get_node("ns=2;i=9")

Kuka_operation  = client.get_node("ns=2;i=10")
Lathe_operation = client.get_node("ns=2;i=11")

WorkpieceID = client.get_node("ns=2;i=12")

Conveyor_Status = client.get_node("ns=2;i=13")
Kuka_Status     = client.get_node("ns=2;i=14")
Lathe_Status    = client.get_node("ns=2;i=15")
###################################################################################################

# Flag of switching status
Client2_Machine_status_flag = True
Operation_completion_flag = False

# log data
with open("Group_{}_Machine_Status_Client_2.txt".format(group_number), "a") as f:
    f.write(
        "{:<10}|{:<20}|{:<20}|{:<20}|{:<20}|{:<20}|{:<20}\n".format("Time", "Conveyor Belt", "KUKA Robot", "CNC Lathe",
                                                                    "Workpiece ID", "KUKA Operation",
                                                                    "CNC Lathe Operation"))
    f.write(
        "{:<10}|{:<10}|{:<9}|{:<10}|{:<9}|{:<10}|{:<9}\n".format(" ", "Status", "R_Time", "Status", "R_Time",
                                                                 "Status", "R_Time", )
    )

# function of multithreading logging operation
def StatusRecord():
    while Client2_Machine_status_flag:

        global Workpiece
        global Current_Operation_log

        with open("Group_{}_Machine_Status_Client_2.txt".format(group_number), "a") as f:
            f.write(
                "{:<10}|{:<10}|{:<9}|{:<10}|{:<9}|{:<10}|{:<9}|{:<20}|{:<20}|{:<20}\n".format(current_time.get_value(),
                                                                                              Conveyor_Status.get_value(),
                                                                                              str(
                                                                                                  time_left_conveyor.get_value()) + 's',
                                                                                              Kuka_Status.get_value(),
                                                                                              str(
                                                                                                  time_left_kuka.get_value()) + 's',
                                                                                              Lathe_Status.get_value(),
                                                                                              str(
                                                                                                  time_left_Lathe.get_value()) + 's',
                                                                                              Workpiece,
                                                                                              Kuka_operation.get_value(),
                                                                                              Lathe_operation.get_value())
            )

        if Operation_completion_flag:  # Condition to close the operation
            with open("Group_{}_Machine_Status_Client_2.txt".format(group_number), "a") as f:
                f.write("{} Completed!\n".format(Current_Operation_log))
                f.write("-" * 130 + "\n")
        sleep(1)

"""
Explanation:
In OPC UA, every server exposes a standard Address Space with well-known root folders. 
One of those is the Objects folder — it’s the entry point where servers put live “things” (instances, variables, and callable methods) that clients interact with.
Objects folder = a standard node (NodeId ns=0;i=85) that contains:built-in Server object,
any custom objects/folders your server creates (e.g., a parameters folder),
callable Method nodes (like Conveyor, Lathe_Prog1, etc.).
In your server, the first two children are objects (Server, parameters), and the rest are your methods.
That’s why Conveyor is at children[2].
Index	Node Type	BrowseName	Purpose
method[0]	Object	Server	Built-in system object (standard)
method[1]	Object	parameters	Your custom folder holding all variables (Equipment_ID, Status_…, etc.)
method[2]	Method	Conveyor	First callable method you added
method[3]	Method	Lathe_Prog1	Second callable method
method[4]	Method	Lathe_Prog2	Third callable method
method[5]	Method	Kuka_Prog1	Fourth callable method
method[6]	Method	Kuka_Prog2	Fifth callable method
"""

#############################################################################################
# Assigning method node ID to the variable
Start_Conveyor_prog = method[2]  # Example
Start_Kuka_Prog2 = method[6]   
#############################################################################################

# Adding and starting a new thread
Add_new_thread = threading.Thread(target=StatusRecord)
Add_new_thread.start()

# data log
with open("Group_{}_Progress_Client_2.txt".format(group_number), "a") as f:
    ctime = str(datetime.now().time())[:-7]
    f.write("{} - Loading operation list\n".format(ctime))
    print("{} - Loading operation list".format(ctime))
    print("There are {} operations from Company 2".format(len(Company_2_operation_list)))
    sleep(1)
    f.write("There are {} Requests in the Operation List\n".format(len(Company_2_operation_list)))
    sleep(1)

index = 1
# Loops for Initiating company's operation list
for Current_operation in Company_2_operation_list:

    Operation_completion_flag = False  # Set to true when operation is completed

    # Conveyor and Kuka status check
    while Conveyor_Status.get_value() != "Idle    " or Kuka_Status.get_value() != "Idle    ":
        sleep(0.5)

    # Lathe status check
    if time_left_Lathe.get_value() == "-":
        pass
    else:
        # Loop until Lathe status occupied
        while time_left_Lathe.get_value() != 0 or (
                int(time_left_Lathe.get_value()) <= 7 and Lathe_Status.get_value() != "Idle    "):
            # Condition to break Loop when lathe is idle
            if time_left_Lathe.get_value() != 0 or time_left_Lathe.get_value() != "-":
                break
            sleep(0.5)

    # data log
    print("-" * 30 + "OPERATION ({})".format(index) + "-" * 30)
    print("Starting {}".format(Current_operation))
    with open("Group_{}_Progress_Client_2.txt".format(group_number), "a") as f:
        f.write("-" * 65 + "\n")
        f.write("Starting {}\n".format(Current_operation))

    # Status check before calling conveyor program
    if Conveyor_Status.get_value() == "Idle    ":

        #############################################################################################
        # Assigning workpiece data and calling Start_Conveyor_prog on server program
        # TODO: add code to link conveyor program start method and pass the current operation detail
        Workpiece = objects_node.call_method(Start_Conveyor_prog, Current_operation)
        #############################################################################################

    else:
        # If lathe occupied waiting until lathe is idle
        while Conveyor_Status.get_value() != "Idle    " or Kuka_Status.get_value() != "Idle    ":
            pass

        if time_left_Lathe.get_value() == "-":
            pass
        else:
            while (int(time_left_Lathe.get_value()) <= 7 and Lathe_Status.get_value() != "Idle    "):
                pass
        # Calling conveyor program
        Workpiece = objects_node.call_method(Start_Conveyor_prog, Current_operation)

    # data log
    print("{} - Initialising Conveyor Belt".format(current_time.get_value()))

    # data log
    with open("Group_{}_Progress_Client_2.txt".format(group_number), "a") as f:
        f.write("{} - Transferring a New Workpiece with ID: {}\n".format(current_time.get_value(), Workpiece))

    # Waiting for conveyor operation to complete
    while time_left_conveyor.get_value() != 0 and Conveyor_Status.get_value() != "Idle    ":
        pass

    # data log
    with open("Group_{}_Progress_Client_2.txt".format(group_number), "a") as f:
        f.write("{} - Connecting to KUKA robot\n".format(current_time.get_value()))

    # Conditional loop for different operation
    if Current_operation == "Operation C":  # Operation C (Measurement)

        print("{} - Arriving the Destination on Conveyor Belt".format(current_time.get_value()))

        # Data log
        print("{} - Starting Kuka Robot Operation ---> Measurement Started".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_2.txt".format(group_number), "a") as f:
            f.write("{} - Starting Kuka Robot Operation ---> Measurement Started\n".format(current_time.get_value()))

        #############################################################################################
        # TODO add code to link Start_Kuka_Prog2 program start method
        # starting Start_Kuka_Prog2 program on kuka
        return_value_kuka_prog2 = objects_node.call_method(Start_Kuka_Prog2)
        #############################################################################################

        sleep(1)

        # Waiting for kuka operation to complete
        while time_left_kuka.get_value() != 0 and Kuka_Status.get_value() != "Idle    " and Kuka_operation.get_value() == "Measurement":
            pass

        # Data log
        print("{} - KUKA Operation Measurement Completed".format(current_time.get_value()))
        with open("Group_{}_Progress_Client_2.txt".format(group_number), "a") as f:
            f.write("{} - KUKA Operation Measurement Completed\n".format(current_time.get_value()))
        sleep(0.5)

    else:  # invalid operation in the list
        print("!!!ERROR!!! Invalid operation included!\n")
        sys.exit()

    ctime = str(datetime.now().time())[:-7]
    print("{} - {} Completed ".format(ctime, Current_operation))
    with open("Group_{}_Progress_Client_2.txt".format(group_number), "a") as f:
        f.write("{} - {} Completed\n".format(ctime, Current_operation))

    index += 1

    # Storing current operation information in a variable
    global Current_Operation_log
    Current_Operation_log = Current_operation

    # Assigning completion flag
    Operation_completion_flag = True

    sleep(1.1)

# status flag
Client2_Machine_status_flag = False
