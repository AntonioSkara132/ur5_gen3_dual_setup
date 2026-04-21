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

def launch_setup(context, *args, **kwargs):
    # Initialize Arguments
    ur_type = LaunchConfiguration("ur_type")
    safety_limits = LaunchConfiguration("safety_limits")
    safety_pos_margin = LaunchConfiguration("safety_pos_margin")
    safety_k_position = LaunchConfiguration("safety_k_position")
    
    # Kinova Specific
    kinova_prefix = LaunchConfiguration("kinova_prefix")
    kinova_base_xyz = LaunchConfiguration("kinova_base_xyz")

    # General arguments
    ur_controllers_file = LaunchConfiguration("ur_controllers_file")
    kinova_controllers_file = LaunchConfiguration("kinova_controllers_file")
    tf_prefix = LaunchConfiguration("tf_prefix")
    activate_joint_controller = LaunchConfiguration("activate_joint_controller")
    initial_joint_controller = LaunchConfiguration("initial_joint_controller")
    description_file = LaunchConfiguration("description_file")
    ur_description_file = LaunchConfiguration("ur_description_file")
    kinova_description_file = LaunchConfiguration("kinova_description_file")
    launch_rviz = LaunchConfiguration("launch_rviz")
    rviz_config_file = LaunchConfiguration("rviz_config_file")
    gazebo_gui = LaunchConfiguration("gazebo_gui")
    world_file = LaunchConfiguration("world_file")


    ur_cm_path = PathJoinSubstitution(["ur", "controller_manager"])
    kinova_cm_path = PathJoinSubstitution(["kinova", "controller_manager"])

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
    ur_robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            ur_description_file,
            " ",
            "safety_limits:=",
            safety_limits,
            " ",
            "safety_pos_margin:=",
            safety_pos_margin,
            " ",
            "safety_k_position:=",
            safety_k_position,
            " ",
            "name:=",
            "ur",
            " ",
            "ur_type:=",
            ur_type,
            " ",
            "tf_prefix:=",
            "ur_",
            " ",
            "simulation_controllers:=",
            ur_controllers_file,
            " ",
            "ros_namespace:=",
            "ur",
        ]
    )

    kortex_robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            kinova_description_file,
            " ",
            "robot_ip:=xxx.yyy.zzz.www",
            " ",
            "name:=",
            "gen3",
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
            "prefix:=",
            "kinova_",
            " ",
            "ros_namespace:=",            
            "kinova",
            " ",
            "sim_gazebo:=",
            "true",
            " ",
            "simulation_controllers:=",
            kinova_controllers_file,
            " ",
            "gripper:=",
            "false",
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
    ur_robot_description = {"robot_description": ur_robot_description_content}
    kinova_robot_description = {"robot_description": kortex_robot_description_content}
            
    
    # cm_path needs to be defined for the spawners
    #cm_path = [robot_namespace, "/controller_manager"]

    kinova_robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[{"use_sim_time": True}, kinova_robot_description],
        namespace="kinova",
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[{"use_sim_time": True}, ur_robot_description],
    )
    ur_robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[{"use_sim_time": True}, ur_robot_description],
        namespace="ur",
        # remappings = [
        #     ('/joint_states', 'joint_states'),
        #     ('/robot_description', 'robot_description'),
        #],
    )

    # Spawner for the UR5
    # joint_state_broadcaster_spawner = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["joint_state_broadcaster", "--controller-manager", cm_path],
    #     #namespace=robot_namespace,
    # )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=["-string", ur_robot_description_content, "-name", "dual_robot_system"],
        #namespace=robot_namespace,
    )
    
    
    gz_sim_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
        #namespace=robot_namespace,
    )

    gz_launch_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
        ),
        launch_arguments={
            "gz_args": IfElseSubstitution(
                gazebo_gui,
                if_value=[" -r -v 4 ", world_file],
                else_value=[" -s -r -v 4 ", world_file],
            )
        }.items(),
    )


    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(launch_rviz),
        #namespace=robot_namespace,
    )

    
    ur_joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", ur_cm_path],
        #namespace="ur",
    )
    
    # There may be other controllers of the joints, but this is the initially-started one
    ur_initial_joint_controller_spawner_started = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[initial_joint_controller, "-c", ur_cm_path],
        condition=IfCondition(activate_joint_controller),
        #namespace="ur"
    )
    ur_initial_joint_controller_spawner_stopped = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[initial_joint_controller, "-c", ur_cm_path, "--stopped"],
        condition=UnlessCondition(activate_joint_controller),
        #namespace="ur",
    )

    kinova_joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", kinova_cm_path],
        #namespace="kinova",
    )

    kinova_initial_joint_controller_spawner_started = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[initial_joint_controller, "-c", kinova_cm_path],
        condition=IfCondition(activate_joint_controller),
        #namespace="kinova",
    )
    kinova_initial_joint_controller_spawner_stopped = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[initial_joint_controller, "-c", kinova_cm_path, "--stopped"],
        condition=UnlessCondition(activate_joint_controller),
        #namespace="kinova",
    )

    # Delay rviz start after `joint_state_broadcaster`
    # 1. Start Kinova spawner after UR spawner finishes
    delay_kinova_after_ur = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=ur_joint_state_broadcaster_spawner,
            on_exit=[kinova_joint_state_broadcaster_spawner],
        )
    )
    
    # 2. Start RViz after Kinova spawner finishes
    delay_rviz_after_kinova = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=kinova_joint_state_broadcaster_spawner,
            on_exit=[rviz_node],
        ),
        condition=IfCondition(launch_rviz),
    )


    # Return list of nodes (Omitted bridge and Gazebo launch for brevity, keep yours)
    return [
        ur_robot_state_publisher_node,
        #kinova_robot_state_publisher_node,
        ur_joint_state_broadcaster_spawner,
        #delay_kinova_after_ur,
        #kinova_joint_state_broadcaster_spawner, no needed becuse of delay kinova
        ur_initial_joint_controller_spawner_started,
        ur_initial_joint_controller_spawner_stopped,
        #delay_rviz_after_kinova,
        #kinova_initial_joint_controller_spawner_started,
        #kinova_initial_joint_controller_spawner_stopped,
        rviz_node,
        gz_spawn_entity,
        gz_launch_description,
        gz_sim_bridge,
    ]

def generate_launch_description():
    declared_arguments = []
    
    # Existing UR arguments
    declared_arguments.append(DeclareLaunchArgument("ur_type", default_value="ur5"))
    declared_arguments.append(DeclareLaunchArgument("safety_limits", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument("safety_pos_margin", default_value="0.15"))
    declared_arguments.append(DeclareLaunchArgument("safety_k_position", default_value="20"))
    declared_arguments.append(DeclareLaunchArgument("tf_prefix", default_value="ur_"))

    # NEW: Kinova specific arguments
    declared_arguments.append(
        DeclareLaunchArgument("kinova_prefix", default_value="kinova_", description="Prefix for Kinova joints")
    )
    declared_arguments.append(
        DeclareLaunchArgument("kinova_base_xyz", default_value="1.2 0 0", description="Mounting position of Kinova")
    )

    # General configuration
    declared_arguments.append(DeclareLaunchArgument("description_file", default_value=PathJoinSubstitution([FindPackageShare("dual_description"), "urdf", "dual.urdf.xacro"])))
    declared_arguments.append(DeclareLaunchArgument("ur_description_file", default_value=PathJoinSubstitution([FindPackageShare("ur_simulation_gz"), "urdf", "ur_gz.urdf.xacro"])))
    declared_arguments.append(DeclareLaunchArgument("kinova_description_file", default_value=PathJoinSubstitution([FindPackageShare("kortex_description"), "robots", "kinova.urdf.xacro"])))
    
    declared_arguments.append(DeclareLaunchArgument("ur_controllers_file", default_value=PathJoinSubstitution([FindPackageShare("dual_description"), "config", "ur_controllers.yaml"])))
    declared_arguments.append(DeclareLaunchArgument("kinova_controllers_file", default_value=PathJoinSubstitution([FindPackageShare("dual_description"), "config", "kinova_controllers.yaml"])))

    declared_arguments.append(DeclareLaunchArgument("launch_rviz", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument("gazebo_gui", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument("world_file", default_value="empty.sdf"))
    declared_arguments.append(DeclareLaunchArgument("initial_joint_controller", default_value="joint_trajectory_controller"))
    declared_arguments.append(DeclareLaunchArgument("activate_joint_controller", default_value="true"))
    declared_arguments.append(DeclareLaunchArgument("rviz_config_file", default_value=""))
    

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
