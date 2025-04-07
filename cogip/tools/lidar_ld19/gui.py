import numpy as np
from matplotlib import animation, pyplot
from numpy.typing import NDArray


def start_gui(lidar_points: NDArray):
    print("Starting plot GUI")

    # Create a polar plot
    fig, ax = pyplot.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("black")  # Set figure background to black
    ax.set_facecolor("black")  # Set axes background to black
    ax.set_ylim(0, 3100)

    # Set foreground elements to red
    ax.tick_params(colors="white")
    ax.spines["polar"].set_color("red")
    ax.grid(color="red", linestyle="--", linewidth=0.5)
    ax.set_title("Real-Time Lidar Data", va="bottom", color="white")

    # Initialize scatter plot with dummy data
    initial_angles = np.radians(np.arange(360))
    initial_distances = np.zeros(360)
    initial_colors = np.zeros(360)
    scatter = ax.scatter(initial_angles, initial_distances, c=initial_colors, cmap="RdYlGn", s=5, vmin=0, vmax=255)
    cbar = pyplot.colorbar(scatter, label="Intensity (0 = red, 255 = green)")
    cbar.ax.yaxis.label.set_color("white")
    cbar.ax.tick_params(colors="white")

    # Configure plot appearance
    ax.set_theta_direction(-1)  # Reverse direction
    ax.set_theta_offset(np.pi / 2.0)  # 0 degrees is upwards

    # Function to handle zooming
    def on_scroll(event):
        current_ylim = ax.get_ylim()
        zoom_factor = 1.1 if event.button == "down" else 0.9  # Zoom in/out
        new_ylim = [limit * zoom_factor for limit in current_ylim]

        # Limit the zoom range
        new_ylim[0] = max(0, new_ylim[0])
        new_ylim[1] = min(5000, new_ylim[1])  # Prevent excessive zoom out
        ax.set_ylim(new_ylim)
        pyplot.draw()

    # Connect the scroll event to the handler
    fig.canvas.mpl_connect("scroll_event", on_scroll)

    # Animation update function
    def update(frame):
        last = np.where(lidar_points[:, 0] == -1)[0]
        if len(last) > 0:
            last = last[0]
        else:
            last = len(lidar_points)
        angles = np.radians(lidar_points[:last, 0])
        distances = lidar_points[:last, 1]
        intensities = lidar_points[:last, 2]

        # Update scatter plot
        scatter.set_offsets(np.column_stack((angles, distances)))
        scatter.set_array(intensities)  # Update colors
        return (scatter,)

    try:
        # Animate the plot
        _ = animation.FuncAnimation(fig, update, interval=100, blit=True, cache_frame_data=False)
        pyplot.show()
    except KeyboardInterrupt:
        pass

    print("Exiting plot GUI.")
