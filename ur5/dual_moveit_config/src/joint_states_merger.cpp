#include <chrono>
#include <functional>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "sensor_msgs/msg/joint_state.hpp"

using namespace std::chrono_literals;

/* This example creates a subclass of Node and uses std::bind() to register a
* member function as a callback from the timer. */

class JointStateMerger : public rclcpp::Node
{
  public:
    JointStateMerger()
    : Node("minimal_publisher"), count_(0)
    {
      publisher_ = this->create_publisher<std_msgs::msg::String>("/joint_states", 10);
      
      ur_subscription_ = this->create_subscription<std_msgs::msg::String>(
      "/ur/joint_states", 10, std::bind(&JointStateMerger::topic_callback, this, _1));
      
      kinova_subscription_ = this->create_subscription<std_msgs::msg::String>(
      "/kinova/joint_states", 10, std::bind(&JointStateMerger::topic_callback, this, _1));
      
    }

  private:
    void ur_callback(const sensor_msgs::msg::JointStates::SharedPtr msg) const
    {
      RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg->data.c_str());
      sensor_msgs::msg::JointStates::SharedPtr new_msg
      new_msg->position[0] = 
    }

    void kinova_callback(const sensor_msgs::msg::JointStates::SharedPtr msg) const
    {
      RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg->data.c_str());
    }
    rclcpp::Subscription<sensor_msgs::msg::JointStates>::SharedPtr ur_subscription_;
    rclcpp::Subscription<sensor_msgs::msg::JointStates>::SharedPtr kinova_subscription_;
    rclcpp::Publisher<std_msgs::msg::JointStates>::SharedPtr publisher_;

    size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalPublisher>());
  rclcpp::shutdown();
  return 0;
}
