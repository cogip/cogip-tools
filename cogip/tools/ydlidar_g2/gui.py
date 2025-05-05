import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.backend_bases import MouseEvent
from matplotlib.collections import PathCollection
from matplotlib.patches import Ellipse
from numpy.typing import NDArray
from sklearn.cluster import DBSCAN


class LidarObstacleTracker:
    def __init__(
        self,
        lidar_coords: NDArray,
        lidar_offset: tuple[float, float],
        eps: float = 30.0,
        min_samples: int = 6,
        update_interval: int = 100,
    ):
        """
        Initialize the real-time Lidar obstacle tracker

        Args:
            lidar_coords: 2D NDArray with shape (MAX_LIDAR_DATA_COUNT, 2) containing x and y global coordinates
            lidar_offset: Lidar offset from robot center
            eps: DBSCAN clustering parameter
            min_samples: Minimum points for cluster formation
            update_interval: Visualization update interval
        """
        # Use default pose if not provided
        self.lidar_coords = lidar_coords
        self.lidar_offset = lidar_offset
        self.eps = eps
        self.min_samples = min_samples
        self.update_interval = update_interval
        self.view_radius = 2500
        self.clusters: list[NDArray] = []
        self.obstacle_properties: list[tuple[float, float, float, float]] = []

        # Initialize plot and data containers
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.setup_plot()

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
            self.lidar_offset[1],
            self.lidar_offset[0],
            c="blue",
            s=80,
            marker="o",
            label="Lidar",
        )

        # Animation setup
        self.animation: FuncAnimation | None = None

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
        self.ax.set_xlim((self.view_radius, -self.view_radius))
        self.ax.set_ylim((-self.view_radius, self.view_radius))

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

    def estimate_obstacle_properties(self, clusters: list[NDArray]) -> list[tuple[float, float, float]]:
        """
        Estimates position and size of obstacles from clusters

        Args:
            clusters: List of clusters, each cluster being a set of points

        Returns:
            List of tuples (center_x, center_y, radius) for each obstacle
        """
        obstacle_properties = []

        for cluster in clusters:
            center_x = np.mean(cluster[:, 0])
            center_y = np.mean(cluster[:, 1])

            # Calculate the maximum distance from center in x and y directions
            # This will be used as the radius of the circle
            radius_x = np.max(np.abs(cluster[:, 0] - center_x))
            radius_y = np.max(np.abs(cluster[:, 1] - center_y))
            radius = max(radius_x, radius_y, 20)  # Minimum radius of 20

            obstacle_properties.append((center_x, center_y, radius))

        return obstacle_properties

    def update_plot(self, frame):
        """Updates the visualization with current data"""
        lidar_coords = self.lidar_coords[: np.argmax(self.lidar_coords[:, 0] == -1)].copy()
        self.clusters = self.cluster_obstacles(lidar_coords)
        self.obstacle_properties = self.estimate_obstacle_properties(self.clusters)

        # Update points scatter
        self.points_scatter.set_offsets(np.column_stack((lidar_coords[:, 1], lidar_coords[:, 0])))

        # Clear previous cluster scatters and obstacle visualizations
        for scatter in self.cluster_scatters:
            scatter.remove()
        self.cluster_scatters = []

        for circle in self.obstacle_circles:
            circle.remove()
        self.obstacle_circles = []

        # Create color map for clusters that works well with dark theme
        colors = plt.cm.plasma(np.linspace(0, 1, max(1, len(self.clusters))))

        # Draw new clusters
        for i, cluster in enumerate(self.clusters):
            scatter = self.ax.scatter(
                cluster[:, 1],
                cluster[:, 0],
                c=[colors[i]],
                s=20,
                label=f"Cluster {i}" if i == 0 else "",
            )
            self.cluster_scatters.append(scatter)

        # Draw obstacle circles and labels
        for i, (center_x, center_y, radius) in enumerate(self.obstacle_properties):
            # Create ellipse for the obstacle
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

        # Limit the zoom range
        x_left = max(-self.view_radius, x_left)
        x_right = min(self.view_radius, x_right)
        y_bottom = max(-self.view_radius, y_bottom)
        y_top = min(self.view_radius, y_top)

        # Apply the new limits
        self.ax.set_xlim(x_left, x_right)
        self.ax.set_ylim(y_bottom, y_top)

        # Redraw the plot
        plt.draw()


def start_gui(lidar_coords: NDArray, lidar_offset: tuple[float, float]):
    print("Starting plot GUI")
    tracker = LidarObstacleTracker(
        lidar_coords=lidar_coords,
        lidar_offset=lidar_offset,
    )

    # Start visualization
    tracker.start_animation()
    try:
        plt.show()
    except KeyboardInterrupt:
        pass

    print("Exiting plot GUI.")
