import typing

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backend_bases import MouseEvent
from matplotlib.collections import PathCollection
from matplotlib.patches import Ellipse

if typing.TYPE_CHECKING:
    from cogip.tools.detector_pami.detector import Detector


class DetectorGUI:
    def __init__(self, detector: "Detector"):
        """
        Initialize the GUI for the detector.

        Args:
            detector: Reference to the Detector instance for accessing shared data.
        """
        self.detector = detector

        # Initialize plot and data containers
        self.fig, self.ax = plt.subplots(figsize=(10, 10))

        # Set figure and axes background color
        self.fig.patch.set_facecolor("#2E2E2E")
        self.ax.set_facecolor("#1E1E1E")

        # Set labels and title with light colors
        self.ax.set_xlabel("Y (mm)", color="#CCCCCC")
        self.ax.set_ylabel("X (mm)", color="#CCCCCC")
        self.ax.set_title("Real-time Obstacle Detection", color="#FFFFFF", fontweight="bold")

        # Customize grid
        self.ax.grid(True, color="#555555", linestyle="-", linewidth=0.5, alpha=0.7)

        # Customize axis appearance
        self.ax.spines["bottom"].set_color("#555555")
        self.ax.spines["top"].set_color("#555555")
        self.ax.spines["left"].set_color("#555555")
        self.ax.spines["right"].set_color("#555555")

        # Customize tick parameters
        self.ax.tick_params(axis="both", colors="#CCCCCC")

        # Invert x-axis and set equal aspect ratio
        self.ax.invert_xaxis()
        self.ax.axis("equal")

        # Configure legend with dark theme colors
        self.ax.legend(facecolor="#333333", edgecolor="#555555", labelcolor="#CCCCCC")

        # Set initial view range
        view_radius = self.detector.properties.max_distance * 1.2
        self.ax.set_xlim((view_radius, -view_radius))
        self.ax.set_ylim((-view_radius, view_radius))

        # Connect the scroll event to the handler
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)

        # Visualization elements
        self.points_scatter = self.ax.scatter([], [], c="gray", s=5, label="Detected Points")
        self.cluster_scatters: list[PathCollection] = []
        self.obstacle_circles: list[Ellipse] = []

        # Robot and Lidar markers
        self.robot_marker = self.ax.scatter(
            0,
            0,
            c="red",
            s=100,
            marker="*",
            label="Robot",
        )

        # Calculate Lidar position
        self.lidar_marker = self.ax.scatter(
            self.detector.LIDAR_OFFSET_Y,
            self.detector.LIDAR_OFFSET_X,
            c="blue",
            s=80,
            marker="o",
            label="Lidar",
        )

        # Animation setup
        self.animation: FuncAnimation | None = None

    def start_animation(self):
        """Starts the real-time visualization."""
        plt.rcParams["axes.prop_cycle"] = plt.cycler(color=plt.cm.plasma(np.linspace(0, 1, 10)))

        self.animation = FuncAnimation(
            self.fig,
            self.update_plot,
            interval=200,
            blit=False,
            cache_frame_data=False,
        )

    def update_robot_pose(self):
        """Update robot pose on the GUI."""
        if not self.detector.shared_pose_current_buffer:
            return

        pose_current = self.detector.shared_pose_current_buffer.last
        x = pose_current.x
        y = pose_current.y
        angle = pose_current.angle

        self.robot_marker.set_offsets([y, x])

        angle_rad = np.radians(-angle)
        lidar_offset_rotated = np.array(
            [
                self.detector.LIDAR_OFFSET_Y * np.cos(angle_rad) - self.detector.LIDAR_OFFSET_X * np.sin(angle_rad),
                self.detector.LIDAR_OFFSET_Y * np.sin(angle_rad) + self.detector.LIDAR_OFFSET_X * np.cos(angle_rad),
            ]
        )
        lidar_x = x + lidar_offset_rotated[1]
        lidar_y = y + lidar_offset_rotated[0]
        self.lidar_marker.set_offsets([lidar_y, lidar_x])

    def update_plot(self, frame):
        """Updates the visualization with current data."""
        self.update_robot_pose()

        if self.detector.shared_lidar_coords is None:
            return

        lidar_coords = self.detector.shared_lidar_coords[
            : np.argmax(self.detector.shared_lidar_coords[:, 0] == -1)
        ].copy()
        self.points_scatter.set_offsets(np.column_stack((lidar_coords[:, 1], lidar_coords[:, 0])))

        for scatter in self.cluster_scatters:
            scatter.remove()
        self.cluster_scatters = []

        for circle in self.obstacle_circles:
            circle.remove()
        self.obstacle_circles = []

        colors = plt.cm.plasma(np.linspace(0, 1, len(self.detector.clusters) + 1))

        for i, cluster in enumerate(self.detector.clusters):
            scatter = self.ax.scatter(
                cluster[:, 1],
                cluster[:, 0],
                c=[colors[i]],
                s=20,
            )
            self.cluster_scatters.append(scatter)

        for i, obstacle in enumerate(self.detector.shared_detector_obstacles):
            center_x = obstacle.x
            center_y = obstacle.y
            radius = obstacle.radius
            circle = Ellipse(
                (center_y, center_x),
                width=radius * 2,
                height=radius * 2,
                fill=False,
                edgecolor=colors[i],
                linewidth=2,
                alpha=0.8,
            )
            self.ax.add_patch(circle)
            self.obstacle_circles.append(circle)

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def on_scroll(self, event: MouseEvent):
        """Handle scroll events for zooming."""
        if event.inaxes != self.ax:
            return

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        x_data, y_data = event.xdata, event.ydata
        zoom_factor = 1.1 if event.button == "down" else 0.9

        x_left = x_data - zoom_factor * (x_data - xlim[0])
        x_right = x_data + zoom_factor * (xlim[1] - x_data)
        y_bottom = y_data - zoom_factor * (y_data - ylim[0])
        y_top = y_data + zoom_factor * (ylim[1] - y_data)

        view_radius = self.detector.properties.max_distance * 1.2
        x_left = max(-view_radius, x_left)
        x_right = min(view_radius, x_right)
        y_bottom = max(-view_radius, y_bottom)
        y_top = min(view_radius, y_top)

        self.ax.set_xlim(x_left, x_right)
        self.ax.set_ylim(y_bottom, y_top)

        plt.draw()
