#!/usr/bin/env python3
"""Export recorded commands/poses to CSV and plot them on a common bag clock."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rosbag


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("analysis"))
    args = parser.parse_args()
    commands, poses = [], []
    with rosbag.Bag(str(args.bag), "r") as bag:
        start = bag.get_start_time()
        for topic, msg, stamp in bag.read_messages(topics=["/turtle1/cmd_vel", "/turtle1/pose"]):
            elapsed = stamp.to_sec() - start
            if topic == "/turtle1/cmd_vel":
                commands.append((elapsed, msg.linear.x, msg.angular.z))
            else:
                poses.append((elapsed, msg.x, msg.y, msg.theta, msg.linear_velocity, msg.angular_velocity))
    if not commands or not poses:
        parser.error("Bag must contain both /turtle1/cmd_vel and /turtle1/pose messages")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, header, rows in [
        ("cmd_vel.csv", ["time_s", "linear_x", "angular_z"], commands),
        ("pose.csv", ["time_s", "x", "y", "theta_rad", "linear_velocity", "angular_velocity"], poses),
    ]:
        with (args.output_dir / name).open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(rows)
    ct, cv, cw = zip(*commands)
    pt, x, y, theta, pv, pw = zip(*poses)
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(ct, cv, label="cmd linear.x")
    axes[0].plot(pt, pv, label="pose linear_velocity", alpha=0.7)
    axes[0].set_ylabel("Linear velocity (turtlesim units/s)")
    axes[1].plot(ct, cw, label="cmd angular.z")
    axes[1].plot(pt, pw, label="pose angular_velocity", alpha=0.7)
    axes[1].set_ylabel("Angular velocity (rad/s)")
    axes[1].set_xlabel("Time since bag start (s)")
    for axis in axes:
        axis.grid(True)
        axis.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "velocity_time.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for axis, values, label in zip(axes, (x, y, theta), ("x", "y", "theta (rad, wrapped)")):
        axis.plot(pt, values)
        axis.set_ylabel(label)
        axis.grid(True)
    axes[-1].set_xlabel("Time since bag start (s)")
    fig.tight_layout()
    fig.savefig(args.output_dir / "position_time.png", dpi=160)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6, 6))
    axis.plot(x, y)
    axis.set(xlabel="x", ylabel="y", title="Recorded turtle trajectory")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True)
    fig.tight_layout()
    fig.savefig(args.output_dir / "trajectory.png", dpi=160)
    plt.close(fig)
    print(f"Read {len(commands)} commands and {len(poses)} poses")
    print(f"CSV and plots saved to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
