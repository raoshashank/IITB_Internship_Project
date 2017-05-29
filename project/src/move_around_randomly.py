#!/usr/bin/env python
import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from math import pi,atan2
from random import randint
import numpy as np
from nav_msgs.msg import Odometry
from project.srv import direction,directionRequest,directionResponse,dirturn,dirturnRequest,dirturnResponse 

def callback2(msg):
    global feedback
    feedback=msg

#To move forward to enter corridoor after turn
def escape_turn():
    global check
    turn_done=1
    ##condition to enter the next corridor
    while True:
        rospy.loginfo("Escaping..")
        go_forward()
        
        
             
    
    

###now that Diff drive bot is used,P-Controller to be used for all motions.
def go_forward():
    global q,cmd,feedback,flag,rate
    global heading,initial_heading,heading_error 
    global angular_velocity_z,linear_velocity_x
    q[0]=feedback.pose.pose.orientation.w
    q[1]=feedback.pose.pose.orientation.x
    q[2]=feedback.pose.pose.orientation.y
    q[3]=feedback.pose.pose.orientation.z  
    heading=atan2(2*(q[0]*q[3]+q[1]*q[2]),1-2*(q[2]*q[2]+q[3]*q[3]))
    if flag==0:
        initial_heading=heading
        flag=1
    heading_error=initial_heading-heading
    if heading_error>pi:
        heading_error=heading_error-2*pi
    if heading_error<=-pi:
        heading_error=heading_error+2*pi
    angular_velocity_z=-0.8*heading_error
    cmd=Twist()
    cmd.linear.x=linear_velocity_x
    cmd.angular.z=angular_velocity_z
    #rate.sleep()
    pub.publish(cmd)
    rospy.loginfo("Going Forward")



def callback(msg):
    global cmd,data,flag,servcaller,servcaller2,turn_done
    data=msg.ranges
    #go_forward()
    ###find maximas:
    ###check in 3 directions for the free space
    ###slice the ranges array into 3 regions for 3 directions:;left,forward and right

    left_slice=np.asarray(data[700:720])
    left_avg=left_slice.sum()/len(left_slice)
    
    mid_slice=np.asarray(data[355:365])
    mid_avg=mid_slice.sum()/len(mid_slice)
    
    right_slice=np.asarray(data[0:20])
    right_avg=right_slice.sum()/len(right_slice)
    
    check=[left_avg,mid_avg,right_avg]
    rospy.loginfo("Values i found are:"+str(check))    
    count=0
    
    ###Check for node position###
    for i in check:
        if i>5:
            count+=1
    
    if count>=2 :
        rospy.loginfo("I'M AT NODE!")        
        cmd=Twist()
        pub.publish(cmd)
        #rate.sleep()        
        ##params for service1
        params.check=check
        #param for service2
        decision=servcaller(params).response
       # rospy.loginfo(decision)
        
        
        if decision=="R" and turn_done==0:
            #call turn_service_caller with param 0
            params2.angle=pi/2
            servcaller2(params2)
            flag=0
            turn_done=1
            escape_turn()          
            rospy.loginfo("R")
        elif decision=="L" and turn_done==0:
            #call turn_service_caller with param 1
            params2.angle=-pi/2
            servcaller2(params2)
            flag=0
            escape_turn()
            turn_done=1
            rospy.loginfo("L")
            
        
    elif count==0 and mid_avg<0.5:
       rospy.loginfo("I'm at end node!")
       ###Call turn_service_caller with param 2
       params2.angle=pi
       servcaller2(params2)
       flag=0
    
    else:
       go_forward()
       
        
        
if  __name__ == "__main__":
    rospy.init_node('random_mover',anonymous=False)   
    
    q=[0,0,0,0]
    flag=0
    turn_done=0
    initial_heading=0.0 
    heading_error=0.0
    heading=0.0  
    check=[]
    interval_for_angle_measurement=10
    linear_velocity_x=0.1
    angular_velocity_z=0
    params=directionRequest()
    params2=dirturnRequest()
    rate=rospy.Rate(20)
    turn_done=0
    odom=Odometry()
    data=LaserScan()
    feedback=Odometry()
    cmd=Twist()
    
    ##Service1 for deciding direction
    rospy.wait_for_service('/direction_service_server')
    servcaller=rospy.ServiceProxy('/direction_service_server',direction)        
    
    #Service2 for turning in the decided direction
    rospy.wait_for_service('/turn_service_server')
    servcaller2=rospy.ServiceProxy('/turn_service_server',dirturn)
    
    sub_odom=rospy.Subscriber('/bot_0/odom',Odometry,callback2)
    pub=rospy.Publisher('/bot_0/cmd_vel',Twist,queue_size=1)
    
    sub=rospy.Subscriber('/bot_0/laser/scan',LaserScan,callback)
    rospy.spin()
