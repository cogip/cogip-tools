import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.backend_bases import MouseEvent
from matplotlib.collections import PathCollection
from numpy.typing import NDArray
from sklearn.cluster import DBSCAN


class RobotPose:
    """
    Represents the complete pose of a robot in 2D space.

    Attributes:
        x: X-coordinate of the robot's position
        y: Y-coordinate of the robot's position
        angle: Orientation angle in degrees
    """

    def __init__(self, x: float = 0.0, y: float = 0.0, angle: float = 0.0):
        """
        Initialize robot pose

        Args:
            x: X-coordinate
            y: Y-coordinate
            angle: Orientation angle in degrees
        """
        self.x = x
        self.y = y
        self.angle = angle

    def transform_point(self, point: NDArray, lidar_offset: tuple[float, float] = (0.0, 0.0)) -> NDArray:
        """
        Transform a point from Lidar coordinate system to global coordinate system

        Args:
            point: Point in Lidar coordinate system
            lidar_offset: Offset of Lidar from robot center

        Returns:
            Transformed point in global coordinate system
        """
        # Convert angle to radians
        angle_rad = np.radians(-self.angle)

        # Apply lidar offset in robot's coordinate system
        offset_point = point + np.array(lidar_offset)

        # Rotation matrix
        rotation_matrix = np.array(
            [
                [np.cos(angle_rad), np.sin(angle_rad)],
                [-np.sin(angle_rad), np.cos(angle_rad)],
            ]
        )

        # Rotate and translate the point
        rotated_point = rotation_matrix @ offset_point
        global_point = rotated_point + np.array([self.x, self.y])

        return global_point


class LidarObstacleTracker:
    def __init__(
        self,
        lidar_data: NDArray,
        max_distance: float = 2000.0,
        min_intensity: int = 100,
        robot_pose: RobotPose | None = None,
        lidar_offset: tuple[float, float] = (0.0, 75.0),
        eps: float = 30.0,
        min_samples: int = 6,
        update_interval: int = 100,
    ):
        """
        Initialize the real-time Lidar obstacle tracker

        Args:
            lidar_data: 2D NDArray with shape (MAX_LIDAR_DATA_COUNT, 3) containing angle, distance and intensity
            max_distance: Maximum detection distance
            min_intensity: Minimum intensity threshold
            robot_pose: Initial robot pose (RobotPose object)
            lidar_offset: Lidar offset from robot center
            eps: DBSCAN clustering parameter
            min_samples: Minimum points for cluster formation
            update_interval: Visualization update interval
        """
        # Use default pose if not provided
        self.robot_pose = robot_pose if robot_pose is not None else RobotPose()

        self.max_distance = max_distance
        self.min_intensity = min_intensity
        self.lidar_offset = lidar_offset
        self.eps = eps
        self.min_samples = min_samples

        # Initialize plot and data containers
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.setup_plot()

        # Connect the scroll event to the handler
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)

        self.points = np.empty((0, 2))
        self.clusters: list[NDArray] = []
        self.obstacle_properties: list[tuple[float, float, float, float]] = []

        # Visualization elements
        self.points_scatter = self.ax.scatter([], [], c="gray", s=5, label="Detected Points")
        self.cluster_scatters: list[PathCollection] = []
        self.obstacle_rects: list[plt.Rectangle] = []

        # Robot and Lidar markers
        self.robot_marker = self.ax.scatter(
            self.robot_pose.x,
            self.robot_pose.y,
            c="red",
            s=100,
            marker="*",
            label="Robot",
        )

        # Calculate Lidar position
        lidar_x = self.robot_pose.x + self.lidar_offset[0]
        lidar_y = self.robot_pose.y + self.lidar_offset[1]
        self.lidar_marker = self.ax.scatter(
            lidar_x,
            lidar_y,
            c="blue",
            s=80,
            marker="o",
            label="Lidar",
        )

        # Animation setup
        self.animation: FuncAnimation | None = None
        self.update_interval = update_interval
        self.lidar_data = lidar_data

    def setup_plot(self):
        """Configure the plot appearance with dark theme"""
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
        view_radius = self.max_distance * 1.2
        xlim = (self.robot_pose.y + view_radius, self.robot_pose.y - view_radius)
        ylim = (self.robot_pose.x - view_radius, self.robot_pose.x + view_radius)

        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

    def polar_to_cartesian(self, lidar_data: NDArray) -> NDArray:
        """
        Converts polar Lidar data to global Cartesian coordinates

        Args:
            lidar_data: 2D NDArray with shape (360, 2) containing distance and intensity

        Returns:
            NDArray of (x, y) points representing detected obstacles
        """
        obstacle_points = []

        # Iterate over the entire Lidar data
        for angle, distance, intensity in lidar_data:
            if angle < 0:
                break

            # Skip rear-facing Lidar data when Lidar is mounted in PAMI case
            if 110 < angle < 250:
                continue

            # Filter on distance
            if distance >= self.max_distance:
                continue

            # Filter on intensity
            if intensity < self.min_intensity:
                continue

            # Convert Lidar-relative polar to Cartesian
            adjusted_angle = (angle + 90) % 360
            lidar_relative_x = distance * np.cos(np.radians(adjusted_angle))
            lidar_relative_y = distance * np.sin(np.radians(adjusted_angle))

            # Transform point to global coordinates
            global_point = self.robot_pose.transform_point(
                np.array([lidar_relative_x, lidar_relative_y]), self.lidar_offset
            )

            obstacle_points.append(global_point)

        return np.array(obstacle_points) if obstacle_points else np.empty((0, 2))

    def update_robot_pose(self, x: float | None = None, y: float | None = None, angle: float | None = None):
        """
        Update the robot's pose

        Args:
            x: New X-coordinate (upward)
            y: New Y-coordinate (leftward)
            angle: New orientation angle in degrees
        """
        if x is not None:
            self.robot_pose.x = x
        if y is not None:
            self.robot_pose.y = y
        if angle is not None:
            self.robot_pose.angle = angle

        # Update plot limits
        view_radius = self.max_distance * 1.2
        self.ax.set_xlim(self.robot_pose.y + view_radius, self.robot_pose.y - view_radius)
        self.ax.set_ylim(self.robot_pose.x - view_radius, self.robot_pose.x + view_radius)

        # Update robot and Lidar markers (note the coordinate swap)
        self.robot_marker.set_offsets([self.robot_pose.y, self.robot_pose.x])

        # Recalculate Lidar position
        lidar_x = self.robot_pose.x + self.lidar_offset[0]
        lidar_y = self.robot_pose.y + self.lidar_offset[1]
        self.lidar_marker.set_offsets([lidar_y, lidar_x])

    def cluster_obstacles(self, points: NDArray) -> list[NDArray]:
        """
        Groups points into obstacle clusters using DBSCAN

        Args:
            points: NDArray of (x, y) points representing detected obstacles

        Returns:
            List of clusters, each cluster being a set of points belonging to the same obstacle
        """
        if len(points) == 0:
            return []

        db = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(points)
        labels = db.labels_

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        clusters = []
        for i in range(n_clusters):
            cluster_points = points[labels == i]
            clusters.append(cluster_points)

        return clusters

    def estimate_obstacle_properties(self, clusters: list[NDArray]) -> list[tuple[float, float, float, float]]:
        """
        Estimates position and size of obstacles from clusters

        Args:
            clusters: List of clusters, each cluster being a set of points

        Returns:
            List of tuples (center_x, center_y, size_x, size_y) for each obstacle
        """
        obstacle_properties = []

        for cluster in clusters:
            center_x = np.mean(cluster[:, 0])
            center_y = np.mean(cluster[:, 1])

            size_x = np.max(cluster[:, 0]) - np.min(cluster[:, 0])
            size_y = np.max(cluster[:, 1]) - np.min(cluster[:, 1])

            obstacle_properties.append((center_x, center_y, size_x, size_y))

        return obstacle_properties

    def update_plot(self, frame):
        """Updates the visualization with current data"""
        lidar_data = self.lidar_data.copy()
        self.points = self.polar_to_cartesian(lidar_data)

        self.clusters = self.cluster_obstacles(self.points)
        self.obstacle_properties = self.estimate_obstacle_properties(self.clusters)

        # Update points scatter
        if len(self.points) > 0:
            self.points_scatter.set_offsets(self.points)
        else:
            self.points_scatter.set_offsets(np.empty((0, 2)))

        # Clear previous cluster scatters and obstacle visualizations
        for scatter in self.cluster_scatters:
            scatter.remove()
        self.cluster_scatters = []

        for rect in self.obstacle_rects:
            rect.remove()
        self.obstacle_rects = []

        # Create color map for clusters that works well with dark theme
        colors = plt.cm.plasma(np.linspace(0, 1, max(1, len(self.clusters))))

        # Draw new clusters
        for i, cluster in enumerate(self.clusters):
            scatter = self.ax.scatter(
                cluster[:, 0],
                cluster[:, 1],
                c=[colors[i]],
                s=20,
                label=f"Cluster {i}" if i == 0 else "",
            )
            self.cluster_scatters.append(scatter)

        # Draw obstacle rectangles and labels
        for i, (center_x, center_y, size_x, size_y) in enumerate(self.obstacle_properties):
            rect = plt.Rectangle(
                (center_x - size_x / 2, center_y - size_y / 2),
                size_x,
                size_y,
                fill=False,
                edgecolor=colors[i],
                linewidth=2,
            )
            self.ax.add_patch(rect)
            self.obstacle_rects.append(rect)

        # Redraw the figure
        self.fig.canvas.draw_idle()

    def start_animation(self):
        """Starts the real-time visualization"""
        # Set dark theme for the color map (for clusters)
        plt.rcParams["axes.prop_cycle"] = plt.cycler(color=plt.cm.plasma(np.linspace(0, 1, 10)))

        # Continue with original animation code
        self.animation = FuncAnimation(
            self.fig,
            self.update_plot,
            interval=self.update_interval,
            blit=False,
            cache_frame_data=False,
        )

    def on_scroll(self, event: MouseEvent):
        # Ignore if the mouse is not over the axes
        if event.inaxes != self.ax:
            return

        # Get the current limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Get mouse position in data coordinates
        x_data, y_data = event.xdata, event.ydata

        # Calculate zoom factor
        zoom_factor = 1.1 if event.button == "down" else 0.9  # Zoom in/out

        # Calculate new limits maintaining the mouse position as center
        x_left = x_data - zoom_factor * (x_data - xlim[0])
        x_right = x_data + zoom_factor * (xlim[1] - x_data)
        y_bottom = y_data - zoom_factor * (y_data - ylim[0])
        y_top = y_data + zoom_factor * (ylim[1] - y_data)

        # Set new limits
        view_radius = self.max_distance * 1.2

        # Limit the zoom range
        x_left = max(-view_radius, x_left)
        x_right = min(view_radius, x_right)
        y_bottom = max(-view_radius, y_bottom)
        y_top = min(view_radius, y_top)

        # Apply the new limits
        self.ax.set_xlim(x_left, x_right)
        self.ax.set_ylim(y_bottom, y_top)

        # Redraw the plot
        plt.draw()


def start_gui(lidar_points: NDArray):
    print("Starting plot GUI")
    tracker = LidarObstacleTracker(
        lidar_data=lidar_points,
        robot_pose=RobotPose(x=0, y=0, angle=0),
    )

    # Start visualization
    tracker.start_animation()
    try:
        plt.show()
    except KeyboardInterrupt:
        pass

    print("Exiting plot GUI.")
