#!/usr/bin/env python
import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from math import pi,atan2,cos,sqrt,pow
from random import randint
import numpy as np
from nav_msgs.msg import Odometry
from project.srv import direction,directionRequest,directionResponse,dirturn,dirturnRequest,dirturnResponse 
from matrix_op import matrix_op
#from project import vertex
from project.msg import vertex_info,vertices



### Traverse to next nodes 
##test V1-V2-V4-V6-V7

def path_to_next_edge():
    ##to apply djktstra algo here
    global vertex_array
    v2=vertex_array[1]
    v4=vertex_array[3]
    v6=vertex_array[5]
    v7=vertex_array[6]
    return["v2","v4","v6","v7"]

def turn_to_next_vertex(current_v,next_v):
    global odom_feedback,cmd,pub
    tolerance=0.1
    if next_v.x>current_v.x and next_v.y-tolerance<current_v.y<next_v.y:
        return pi/2
    elif next_v.x<current_v.x and next_v.y-tolerance<current_v.y<next_v.y:
        return -pi/2
    elif next_v.y>current_v.y and next_v.x-tolerance<current_v.x<next_v.x:
        return 0
    elif next_v.y<current_v.y and next_v.x-tolerance<current_v.x<next_v.x:
        return pi

    
    


def check_for_vertex_in_array(v_x,v_y):
    global vertex_array
    v_found=vertex_info()
    v_found.tag=""
    tolerance=0.1
    for v in vertex_array:
        if v.x+tolerance < v_x < v.x-tolerance and v.y+tolerance < v_y < v.y-tolerance:
            v_found=v
    rospy.loginfo("found :"+v_found.tag)
    return v_found

def check_for_vertex_in_array_tag(tag):
    global vertex_array
    v_found=vertex_info()
    v_found.tag=""
    for v in vertex_array:
        if v.tag==tag:
            v_found=v
    rospy.loginfo("found :"+v_found.tag)
    return v_found


def forward_by_half_lane_width():
    global data,check,odom_feedback,lane_width,pub

    x_start=odom_feedback.pose.pose.position.x
    y_start=odom_feedback.pose.pose.position.y
    delta=0.05
    error=0
    goal_dst=lane_width/2+delta
    dst=0
    while dst<=goal_dst:
       go_forward()
       dst=sqrt((odom_feedback.pose.pose.position.x-x_start)**2+(odom_feedback.pose.pose.position.y-y_start)**2)

    cmd=Twist()
    pub.publish(cmd)
    rospy.loginfo("Escaped")

    



def go_forward():
    global q,cmd,odom_feedback,flag,rate,heading,initial_heading,heading_error,angular_velocity_z,linear_velocity_x
    q[0]=odom_feedback.pose.pose.orientation.w
    q[1]=odom_feedback.pose.pose.orientation.x
    q[2]=odom_feedback.pose.pose.orientation.y
    q[3]=odom_feedback.pose.pose.orientation.z  
    heading=atan2(2*(q[0]*q[3]+q[1]*q[2]),1-2*(q[2]*q[2]+q[3]*q[3]))
    if flag==0:
        initial_heading=heading
        flag=1
    heading_error=initial_heading-heading
    if heading_error>pi:
        heading_error=heading_error-2*pi
    if heading_error<=-pi:
        heading_error=heading_error+2*pi
    angular_velocity_z=-0.9*heading_error
    cmd=Twist()
    cmd.linear.x=linear_velocity_x
    cmd.angular.z=angular_velocity_z
    pub.publish(cmd)



def odom_callback(msg):
    global odom_feedback
    odom_feedback=msg

def vertices_callback(msg):
    global vertex_array
    vertex_array=msg.v



def laser_callback(msg):
    global check,mid_avg,data
    data=msg.ranges
    check=[data[719],data[360],data[0]]


def orient_to_heading(dir):
    global flag,odom_feedback,heading_cmd,heading,q,cmd ,done,angle,initial_heading,heading_error
    q=[0,0,0,0]
    done=0
    heading_cmd=dir
    while done!=1:
        cmd=Twist()
        q[0]=odom_feedback.pose.pose.orientation.w
        q[1]=odom_feedback.pose.pose.orientation.x
        q[2]=odom_feedback.pose.pose.orientation.y
        q[3]=odom_feedback.pose.pose.orientation.z  
        heading=atan2(2*(q[0]*q[3]+q[1]*q[2]),1-2*(q[2]*q[2]+q[3]*q[3]))
        heading_error=heading_cmd-heading

        if heading_error>pi:
            heading_error=heading_error-2*pi
        if heading_error<=-pi:
            heading_error=heading_error+2*pi
    
    
        if abs(heading_error) < 0.001:
            rospy.loginfo("Turn done!")
            done=1
        else:
            cmd.angular.z=-0.8*heading_error
            pub.publish(cmd)






def main():
    global cmd,data,flag,servcaller,servcaller2,node_found,check,mid_avg,params,params2,heading,odom_feedback,vertex_array,done
    #global vertices
    while not rospy.is_shutdown():
        if check!=[]:
            count=0

            for i in check:
                if i>range_thresh:
                    count+=1

            if count>=2 or (count==0 and data[360]<lane_width/2):
              rospy.loginfo("I'M AT NODE!")
              if count>=2:        
                forward_by_half_lane_width()

              orient_to_heading(pi/2)
              v_found=vertex_info()
              v_x=odom_feedback.pose.pose.position.x
              v_y=odom_feedback.pose.pose.position.y
              v_found=check_for_vertex_in_array(v_x,v_y)
              rospy.loginfo(v_found.tag)
              str=path_to_next_edge()
              rospy.loginfo(str)
              
              for s in str:
                  v_next=check_for_vertex_in_array_tag(s)
                  next_turn=turn_to_next_vertex(v_found,v_next)
                  rospy.loginfo(v_next.tag)
                  rospy.loginfo(next_turn)
                  if next_turn!=0:
                      params2.angle=next_turn
                      servcaller2(params2)
                      flag=0
                
                  while True:
                      go_forward()
                      count_temp=0
                      for i in check:
                        if i>range_thresh:      
                            count+=1
                      if count>=2 or (count==0 and data[360]<lane_width/2):
                        break
            
            else:
                go_forward()

        
if  __name__ == "__main__":
    rospy.init_node('random_mover',anonymous=False)   
    ###########Global Variables############
    bot_no=0
    
    q=[0,0,0,0]
    flag=0
    node_found=0
    initial_heading=0.0 
    heading_error=0.0
    heading=0.0  
    check=[]
    interval_for_angle_measurement=10
    linear_velocity_x=0.1
    angular_velocity_z=0
    
    params=directionRequest()
    params2=dirturnRequest()
    
    rate=rospy.Rate(5)
    
    odom=Odometry()
    data=LaserScan()
    odom_feedback=Odometry()
    cmd=Twist()
    op=matrix_op()
    
    mid_avg=0
    range_thresh=2
    lane_width=2
    vertex_array=[]
    I_R=[]
    ###########Global Variables############

    sub_odom=rospy.Subscriber('/bot_0/odom',Odometry,odom_callback)
    pub=rospy.Publisher('/bot_0/cmd_vel',Twist,queue_size=1)
    
    sub=rospy.Subscriber('/bot_0/laser/scan',LaserScan,laser_callback)
    
    sub_vertex=rospy.Subscriber('/vertices',vertices,vertices_callback)
    pub_vertices=rospy.Publisher('/vertices',vertices,queue_size=1)

    main()
    rospy.spin()
