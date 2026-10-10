# 小乌龟圆周运动实验（ROS 1 Noetic）

从已有 C++ 节点出发，学习参数、launch、rosbag、绘图、rqt 和 Git。

## 1. 理解目录和公式

这是一个 ROS package，位于 `~/catkin_ws/src/turtle_circle_ctrl`。

```text
turtle_circle_ctrl/
├── src/circle_turtle.cpp     # 发布速度的 C++ 节点
├── launch/circle.launch     # 启动小乌龟、控制节点，可选录包
├── scripts/analyze_bag.py   # 读取 bag，导出 CSV 和图片
├── CMakeLists.txt           # 编译规则
├── package.xml             # 包名与依赖
└── README.md
```

`period` 是一圈的周期 T（秒），`amplitude` 是圆半径 R（turtlesim 坐标单位）。
角速度 ω = 2π/T，线速度 v = Rω。默认 T=10、R=1，所以 v 和 ω 的数值均约为 0.6283。
这是恒定速度画圆：速度随时间是水平线，x、y 随时间近似为正弦曲线。
这里“幅值”不是速度的正弦幅值。

在初始位置 (x0,y0)、朝向 θ0 下，理想运动是：

```text
x(t) = x0 + R[sin(θ0 + ωt) - sin(θ0)]
y(t) = y0 - R[cos(θ0 + ωt) - cos(θ0)]
```

默认朝向是向右，圆心在初始位置上方。先用 R=1，过大的圆会碰到窗口边界。

## 2. 编译（先完成这一步）

```bash
source /opt/ros/noetic/setup.bash
cd ~/catkin_ws
catkin_make -DCATKIN_WHITELIST_PACKAGES=turtle_circle_ctrl
source devel/setup.bash
```

本工作空间还有 `flight_controller`，它缺少 `mav_msgs`，所以使用白名单只构建本包。
白名单会保存在 CMake 缓存中。以后其他包的依赖齐全、需要编译整个工作空间时，用：

```bash
catkin_make -DCATKIN_WHITELIST_PACKAGES=""
```

每个新终端先执行 `source ~/catkin_ws/devel/setup.bash`。
它同时加载底层 ROS 和你自己的工作空间环境。

## 3. 用 roslaunch 启动

如果之前已经启动过旧的 `circle_turtle` 和 `turtlesim_node`，先在它们各自终端按 Ctrl+C。
保留原来的 roscore。避免两个控制程序同时向同一速度话题发消息。

```bash
source ~/catkin_ws/devel/setup.bash
roslaunch turtle_circle_ctrl circle.launch period:=10 amplitude:=1
```

如果没有 roscore，roslaunch 会自动启动一个，不需要额外运行 roscore。
`rosrun` 启动单个程序，`roslaunch` 根据 XML 文件一次启动多个程序，并设置参数。
`period:=10` 是传给 launch 的参数，launch 用 `<param>` 写入 ROS 参数服务器。

另开终端查询：

```bash
source ~/catkin_ws/devel/setup.bash
rosparam get /turtle_circle_node
rostopic echo /turtle1/cmd_vel
```

按 Ctrl+C 停止 echo。你应看到 linear.x 和 angular.z 约为 0.6283，其余分量为零。

代码使用 `ros::NodeHandle("~")` 读取私有参数，所以完整参数名是
`/turtle_circle_node/period`、`/turtle_circle_node/amplitude` 和
`/turtle_circle_node/publish_rate`。这些参数在程序启动时读取一次。
修改参数需要停止 launch，再启动，例如：

```bash
roslaunch turtle_circle_ctrl circle.launch period:=6 amplitude:=1.5 publish_rate:=30
```

这个设置让它每 6 秒转一圈，半径 1.5。运行中单独执行 rosparam set 不会立即改变运动。
Ctrl+C 停止控制后，小乌龟可能继续移动约 1 秒，随后由 turtlesim 的速度超时机制停止。

## 4. 用 rosbag 记录（选一种方式）

推荐：先停止上一轮 launch，再启动带录包的 launch：

```bash
mkdir -p ~/catkin_ws/bags
roslaunch turtle_circle_ctrl circle.launch period:=10 amplitude:=1 record:=true
```

记录至少 25 秒（超过两圈），然后在 launch 终端按 Ctrl+C，等它正常退出。
文件保存在 `~/catkin_ws/bags/circle_日期时间.bag`。
必须先创建目录。录包节点订阅 `/turtle1/cmd_vel` 和 `/turtle1/pose`。

另一种方式：在普通 launch 运行时，单独开终端记录：

```bash
source ~/catkin_ws/devel/setup.bash
mkdir -p ~/catkin_ws/bags
rosbag record -O ~/catkin_ws/bags/circle_manual.bag /turtle1/cmd_vel /turtle1/pose
```

先 Ctrl+C 停止录包，再停止控制。此方式文件名固定，下一次请换名字，以免覆盖。
不要同时使用两种录包方式。

查看文件名和消息概况：

```bash
ls -lh ~/catkin_ws/bags/*.bag
rosbag info ~/catkin_ws/bags/你的实际文件名.bag
```

两个 topic 都应存在，cmd_vel 的类型是 geometry_msgs/Twist，pose 是 turtlesim/Pose。
pose 包含 x、y、theta 和实际线速度、角速度。

## 5. Python 分析 bag

本包提供完整脚本，不需要 MATLAB。若 Python 报缺少 matplotlib：

```bash
sudo apt install python3-matplotlib
```

将下面的 `你的实际文件名.bag` 换成上一步看到的文件名：

```bash
source ~/catkin_ws/devel/setup.bash
rosrun turtle_circle_ctrl analyze_bag.py ~/catkin_ws/bags/你的实际文件名.bag --output-dir ~/catkin_ws/analysis
```

输出：

- `velocity_time.png`：发送的线/角速度和 pose 报告的线/角速度相对于时间。
- `position_time.png`：x、y、theta 相对于时间。
- `trajectory.png`：x-y 平面轨迹，应接近圆。
- `cmd_vel.csv`、`pose.csv`：可进一步分析的数据。

时间轴使用 bag 的记录时间，统一减去 bag 起始时间，单位秒。
Twist 和 Pose 都没有 Header，不应把记录时间误当作传感器采样时间。
两个话题分别使用自己的时间戳绘图，不按消息序号强行对齐。
速度通常为常数，x、y 是周期曲线；theta 在 ±π 之间回绕，所以角度曲线有跳变。
启动时可能短暂出现实际速度为零，录包开始也可能稍晚于控制启动。
分析时说明这些现象，并检查 x/y 的重复周期是否接近设定的 period。

## 6. rqt_plot 实时查看速度

让 launch 保持运行，另开终端：

```bash
source ~/catkin_ws/devel/setup.bash
rqt_plot /turtle1/cmd_vel/linear/x /turtle1/cmd_vel/angular/z
```

默认半径为 1，两条线数值相同，会重叠。可以用 amplitude:=1.5 区分两条线。
还可以观察位置：

```bash
rqt_plot /turtle1/pose/x /turtle1/pose/y
```

若命令缺失：`sudo apt install ros-noetic-rqt-plot ros-noetic-rqt-graph`。

## 7. rqt_graph 查看节点和话题关系

```bash
source ~/catkin_ws/devel/setup.bash
rqt_graph
```

点击刷新。选择 Nodes/Topics (all)，取消 Hide 中相关过滤项以显示全部节点和话题。
不同界面版本选项文字可能略有不同。
带录包时应能观察到：

```text
/turtle_circle_node → /turtle1/cmd_vel → /turtlesim
                             └──────→ /circle_recorder
/turtlesim → /turtle1/pose → /circle_recorder
```

rqt_plot 运行时也会显示它对速度话题的订阅。
还可以用命令核对：

```bash
rosnode list
rostopic list
rostopic info /turtle1/cmd_vel
rostopic info /turtle1/pose
```

保存 rqt_plot、rqt_graph 和分析图的截图，作为实验结果。

## 8. Git：先本地保存，再上传 GitHub

本包目录是 Git 仓库；不要把 build/devel 或整个 catkin_ws 上传。
bag 和生成的图片/CSV 被 .gitignore 排除，避免仓库过大。
请把下面的姓名和邮箱替换成自己的（邮箱可用 GitHub 的 noreply 邮箱）：

```bash
cd ~/catkin_ws/src/turtle_circle_ctrl
git config user.name "你的名字"
git config user.email "你的邮箱"
git add .
git commit -m "Add parameterized turtle circle controller, launch and bag analysis"
```

在 GitHub 网页创建空仓库，建议名 `turtle_circle_ctrl`。
不要勾选自动创建 README、.gitignore 或 License，因为本地已准备好文件。
选择你希望的可见性，然后复制仓库 HTTPS 或 SSH 地址。

```bash
git remote add origin https://github.com/你的用户名/turtle_circle_ctrl.git
git push -u origin main
```

这是模板，必须替换用户名和地址。HTTPS 身份验证使用 GitHub 支持的凭据方式，
不要在聊天或代码中填写 token。也可以使用已配置 SSH 的仓库地址。
上传后，在 GitHub 网页确认代码、launch 和脚本都在。
后续修改按 `git add` → `git commit` → `git push` 保存。

## 9. 建议实验顺序

先用默认参数跑通 → 查询参数 → 改周期/半径并重启 → 记录至少两圈 → Python 画图
→ 用 rqt 查看关系 → 本地 Git 提交 → 推送 GitHub。
最后说明：参数取值、速度计算公式、周期和半径是否符合预期，以及节点间如何通信。
