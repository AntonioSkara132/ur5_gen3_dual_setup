from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
    IfElseSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
import os
import yaml

def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path) as file:
            return yaml.safe_load(file)
    except OSError:  # parent of IOError, OSError *and* WindowsError where available
        return None


def launch_setup(context, *args, **kwargs):
    # Initialize Arguments
    ur_type = LaunchConfiguration("ur_type")
    safety_limits = LaunchConfiguration("safety_limits")
    safety_pos_margin = LaunchConfiguration("safety_pos_margin")
    safety_k_position = LaunchConfiguration("safety_k_position")
    
    # Kinova Specific
    kinova_prefix = LaunchConfiguration("kinova_prefix")
    #kinova_base_xyz = LaunchConfiguration("kinova_base_xyz")

    # General arguments
    ur_controllers_file = LaunchConfiguration("ur_controllers_file")
    kinova_controllers_file = LaunchConfiguration("kinova_controllers_file")
    tf_prefix = LaunchConfiguration("tf_prefix")
    activate_joint_controller = LaunchConfiguration("activate_joint_controller")
    initial_ur_joint_controller = LaunchConfiguration("initial_ur_joint_controller")
    initial_kinova_joint_controller = LaunchConfiguration("initial_kinova_joint_controller")
    
    description_file = LaunchConfiguration("description_file")
    launch_rviz = LaunchConfiguration("launch_rviz")
    rviz_config_file = LaunchConfiguration("rviz_config_file")
    gazebo_gui = LaunchConfiguration("gazebo_gui")
    world_file = LaunchConfiguration("world_file")
    use_sim_time = LaunchConfiguration("use_sim_time")
    launch_servo = LaunchConfiguration("launch_servo")


    ur_cm_path = PathJoinSubstitution(["ur", "controller_manager"])
    kinova_cm_path = PathJoinSubstitution(["kinova", "controller_manager"])


    moveit_config = (
        MoveItConfigsBuilder(robot_name="ur", package_name="dual_moveit_config")
        .robot_description_semantic(Path("srdf") / "dual.srdf.xacro", {"name": "dual"})
        .robot_description_kinematics(file_path=get_package_share_directory("dual_moveit_config")+"/config/kinematics.yaml")
        .joint_limits(file_path=get_package_share_directory("dual_moveit_config")+"/config/joint_limits.yaml")
        .planning_pipelines(pipelines=["pilz_industrial_motion_planner", "ompl"])
        .trajectory_execution(file_path=get_package_share_directory("dual_moveit_config")+"/config/moveit_controllers.yaml")
        #.moveit_cpp(file_path=get_package_share_directory("dual_moveit_config")+"/config/motion_planning_api.yaml")
        .to_moveit_configs()
    )
    # The Robot Description Command - Updated for Dual Setup
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ", description_file, " ",
            "safety_limits:=", safety_limits, " ",
            "name:=", "dual", " ",
            "safety_pos_margin:=", safety_pos_margin, " ",
            "safety_k_position:=", safety_k_position, " ",
            "ur_type:=", ur_type, " ",
            "ur_prefix:=", "ur_", " ",
            "kinova_prefix:=", "kinova_", " ",
            #"kinova_base_xyz:=", kinova_base_xyz, " ",
            "ur_simulation_controllers:=", ur_controllers_file, " ",
            
            "kinova_simulation_controllers:=", kinova_controllers_file,
            " ",
            "arm:=",
            "gen3",
            " ",
            "dof:=",
            "7",
            " ",
            "vision:=",
            "false",
            " ",
            "sim_gazebo:=",
            "true",
            " ",
            
        ]
    )

    # gz_spawn_entity = Node(
    #     package="ros_gz_sim",
    #     executable="create",
    #     output="screen",
    #     arguments=[
    #         "-string",
    #         robot_description_content,
    #         "-name",
    #         "ur",
    #         "-allow_renaming",
    #         "true",
    #     ],
    #     #namespace=robot_namespace,
    # )
    
    robot_description = {"robot_description": robot_description_content}
    
    # cm_path needs to be defined for the spawners
    #cm_path = [robot_namespace, "/controller_manager"]

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[{"use_sim_time": True}, robot_description],
    ) 
    
    # robot_state_publisher_node = Node(
    #     package="robot_state_publisher",
    #     executable="robot_state_publisher",
    #     output="both",
    #     parameters=[{"use_sim_time": True}, robot_description],
    #     #namespace="kinova",
    # )
    # ur_robot_state_publisher_node = Node(
    #     package="robot_state_publisher",
    #     executable="robot_state_publisher",
    #     output="both",
    #     parameters=[{"use_sim_time": True}, robot_description],
    #     namespace="ur",
    #     remappings = [
    #         #('/ur/joint_states', 'joint_states'),
    #         #('/ur/robot_description', 'robot_description'),
    #     ],
    # )

    # ... [Keep your RViz and Gazebo nodes as they are in your original file] ...
    # Make sure to use 'cm_path' in your spawner nodes as defined above.

    # Spawner for the UR5
    # joint_state_broadcaster_spawner = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["joint_state_broadcaster", "--controller-manager", cm_path],
    #     #namespace=robot_namespace,
    # )
    
    rviz_node = Node(
        package="rviz2",
        condition=IfCondition(launch_rviz),
        executable="rviz2",
        name="rviz2_moveit",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            #moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            #warehouse_ros_config,
            {
                "use_sim_time": True,
                "robot_description": robot_description_content,
            },
        ],
        #remappings=[('/robot_description', rd_path)],
        #namespace=robot_namespace,
        #namespace="ur",
    )
    
    # kinova_joint_state_broadcaster_spawner = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["joint_state_broadcaster", "--controller-manager", kinova_cm_path],
    #     #namespace="kinova",
    #     #remappings=[("/joint_states", "/joint_states")],
    # )

    # kinova_initial_joint_controller_spawner_started = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=[initial_kinova_joint_controller, "-c", kinova_cm_path],
    #     condition=IfCondition(activate_joint_controller),
    #     #namespace="kinova",
    # )
    # kinova_initial_joint_controller_spawner_stopped = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=[initial_kinova_joint_controller, "-c", kinova_cm_path, "--stopped"],
    #     condition=UnlessCondition(activate_joint_controller),
    #     #namespace="kinova",
    # )

    # delay_kinova_after_ur = RegisterEventHandler(
    #     event_handler=OnProcessExit(
    #         target_action=ur_joint_state_broadcaster_spawner,
    #         on_exit=[kinova_joint_state_broadcaster_spawner],
    #     )
    # )
    
    # # 2. Start RViz after Kinova spawner finishes
    # delay_rviz_after_kinova = RegisterEventHandler(
    #     event_handler=OnProcessExit(
    #         target_action=kinova_joint_state_broadcaster_spawner,
    #         on_exit=[rviz_node],
    #     ),
    #     condition=IfCondition(launch_rviz),
    # )


    # Return list of nodes (Omitted bridge and Gazebo launch for brevity, keep yours)


    wait_robot_description = Node(
        package="ur_robot_driver",
        executable="wait_for_robot_description",
        output="screen",
        #namespace=robot_namespace,
        #remappings=[
        #    ('/robot_description', rd_path),
        #],        
    )
    #ld.add_action(wait_robot_description)

    
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            #warehouse_ros_config,
            {
                "use_sim_time": True,
                #"publish_robot_description_semantic": publish_robot_description_semantic,
                "robot_description": robot_description_content,
            },
        ],
        #remappings=[('/robot_description', rd_path), ('/joint_states', js_path)],
        #namespace=robot_namespace,
    )

    servo_yaml = load_yaml("ur_moveit_config", "config/ur_servo.yaml")
    servo_params = {"moveit_servo": servo_yaml}

    servo_node = Node(
        package="moveit_servo",
        condition=IfCondition(launch_servo),
        executable="servo_node",
        parameters=[            
            moveit_config.to_dict(),
            servo_params,
        ],
        output="screen",
        #namespace="ur",
    )

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("ur_dual_bringup"), "config", "moveit.rviz"]
    )
    

    # ld.add_action(
    #     RegisterEventHandler(
    #         OnProcessExit
    #             target_action=wait_robot_description,
    #             on_exit=[move_group_node, rviz_node, servo_node],
    #         )
    #     ),
    # )

    joint_state_merger = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{
            'source_list': ['/ur/joint_states', '/kinova/joint_states'],
            'rate': 100,  # Publish at 30Hz
            'use_sim_time': True,
        }],
        # Ensure it publishes to the global /joint_states topic
        #remappings=[('/joint_states', 'joint_states')]
    )


    
    return [
        robot_state_publisher_node,
        #robot_state_publisher_node,
        #kinova_robot_state_publisher_node,
        #ur_joint_state_broadcaster_spawner,
        #delay_kinova_after_ur,
        #kinova_joint_state_broadcaster_spawner,
        #delay_rviz_after_kinova,
        #kinova_initial_joint_controller_spawner_started,
        #kinova_initial_joint_controller_spawner_stopped,
        #ur_initial_joint_controller_spawner_started,
        #ur_initial_joint_controller_spawner_stopped,
        #gz_spawn_entity,
        #gz_launch_description,
        #gz_sim_bridge,
        joint_state_merger,
        move_group_node,
        rviz_node,
    ]

def generate_launch_description():
    declared_arguments = []
    
    # Existing UR arguments
    declared_arguments.append(DeclareLaunchArgument("ur_type", default_value="ur5e"))
    declared_arguments.append(DeclareLaunchArgument("safety_limits", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument("safety_pos_margin", default_value="0.15"))
    declared_arguments.append(DeclareLaunchArgument("safety_k_position", default_value="20"))
    declared_arguments.append(DeclareLaunchArgument("tf_prefix", default_value="ur_"))

    # NEW: Kinova specific arguments
    declared_arguments.append(
        DeclareLaunchArgument("kinova_prefix", default_value="kinova_", description="Prefix for Kinova joints")
    )

    # General configuration
    declared_arguments.append(DeclareLaunchArgument("description_file", default_value=PathJoinSubstitution([FindPackageShare("dual_description"), "urdf", "dual.urdf.xacro"])))
    
    declared_arguments.append(DeclareLaunchArgument("ur_controllers_file", default_value=PathJoinSubstitution([FindPackageShare("ur_dual_bringup"), "config", "myur_controller.yaml"])))
    declared_arguments.append(DeclareLaunchArgument("kinova_controllers_file", default_value=PathJoinSubstitution([FindPackageShare("dual_description"), "config", "kinova_controllers.yaml"])))

    declared_arguments.append(DeclareLaunchArgument("launch_rviz", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument("gazebo_gui", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument("world_file", default_value="empty.sdf"))
    declared_arguments.append(DeclareLaunchArgument("initial_ur_joint_controller", default_value="joint_trajectory_controller"))
    declared_arguments.append(DeclareLaunchArgument("initial_kinova_joint_controller", default_value="joint_trajectory_controller"))
    declared_arguments.append(DeclareLaunchArgument("activate_joint_controller", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument("rviz_config_file", default_value=""))
    declared_arguments.append(DeclareLaunchArgument("use_sim_time", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument(
                "launch_servo", default_value="false", description="Launch Servo?"
            ))

    

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
