#include <cmath>
#include <ros/ros.h>
#include <geometry_msgs/Twist.h>

int main(int argc, char **argv)
{
    ros::init(argc, argv, "turtle_circle_node");
    ros::NodeHandle nh;
    ros::NodeHandle private_nh("~");

    // 私有参数：周期（秒）、幅值/半径（turtlesim 坐标单位）、发布频率（Hz）。
    double period, amplitude, publish_rate;
    private_nh.param("period", period, 10.0);
    private_nh.param("amplitude", amplitude, 1.0);
    private_nh.param("publish_rate", publish_rate, 20.0);
    if (!std::isfinite(period) || period <= 0.0 ||
        !std::isfinite(amplitude) || amplitude <= 0.0 ||
        !std::isfinite(publish_rate) || publish_rate <= 0.0) {
        ROS_FATAL("period, amplitude and publish_rate must be finite and positive");
        return 1;
    }

    const double angular_velocity = 2.0 * std::acos(-1.0) / period;
    const double linear_velocity = amplitude * angular_velocity;
    if (!std::isfinite(angular_velocity) || !std::isfinite(linear_velocity)) {
        ROS_FATAL("Computed velocities must be finite");
        return 1;
    }
    ros::Publisher pub = nh.advertise<geometry_msgs::Twist>("/turtle1/cmd_vel", 10);
    ros::Rate rate(publish_rate);
    geometry_msgs::Twist command;
    command.linear.x = linear_velocity;
    command.angular.z = angular_velocity;
    ROS_INFO("Circle: period=%.3f s, radius=%.3f, v=%.3f, omega=%.3f rad/s",
             period, amplitude, linear_velocity, angular_velocity);
    while (ros::ok()) {
        pub.publish(command);
        ros::spinOnce();
        rate.sleep();
    }
    return 0;
}
