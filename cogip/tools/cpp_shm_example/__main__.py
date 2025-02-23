#!/usr/bin/env python3
from cogip.cpp.libraries.models import Coords
from cogip.cpp.libraries.obstacles import ObstacleCircle
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory


def main():
    """
    Usage example for shared memory usage C++ extension.

    During installation of cogip-tools, a script called `cogip-cpp-shm-example`
    will be created using this function as entrypoint.
    """
    name = "/example"

    # In this example, it is not necessary to create multiple SharedMemory objects.
    # It is done to illustrate SharedMemory object from different processes.
    # In the following example, there is no difference between writer and reader objects, only lock usage is important.

    # ==> OWNER process
    # The owner object will be created in only one process,
    # typically cogip-server be cause all other processes are depend on it.
    print("Create owner object.")
    owner = SharedMemory(name, True)

    # ==> WRITER process
    # A writer object will be instantiated by processes that need to write into the shared memory.
    # Each process will get a lock corresponding to the part of the shared memory they want to modify.
    # Typically, `cogip-copilot` will update the `pose_current` part so it get the lock named `PoseCurrent`.
    print("Create writer object.")
    writer = SharedMemory(name)
    writer_lock = writer.get_lock(LockName.PoseCurrent)
    writer_data = writer.get_data()
    writer_pose_current = writer.get_pose_current()
    writer_pose_current_buffer = writer.get_pose_current_buffer()

    writer_lock.start_reading()
    print(" => writer data = ", writer_data)
    writer_lock.finish_reading()

    # ==> READER process
    # A reader object will be instantiated by processes that need to write into the shared memory.
    # Each process will get a lock corresponding to the part of the shared memory they want to read.
    # Typically, `cogip-planner` will read the `pose_current` part so it get the lock named `PoseCurrent`.
    print("Create reader object.")
    reader = SharedMemory(name)
    reader_lock = writer.get_lock(LockName.PoseCurrent)
    reader_data = reader.get_data()
    reader_pose_current = reader.get_pose_current()
    reader_pose_current_buffer = reader.get_pose_current_buffer()
    reader_lock.start_reading()
    print(" => reader data = ", reader_data)
    print(" => reader pose_current = ", reader_pose_current)
    reader_lock.finish_reading()

    # ==> WRITER process
    print("Set pose_current")
    writer_lock.start_writing()
    writer_pose_current.x = 1.0
    writer_pose_current.y = 2.0
    writer_pose_current.angle = 90.0
    writer_lock.finish_writing()
    writer_lock.start_reading()
    print(" => writer pose_current = ", writer_pose_current)
    print(" => writer data = ", writer_data)
    writer_lock.finish_reading()

    # ==> READER process
    reader_lock.start_reading()
    print(" => reader pose_current = ", reader_pose_current)
    print(" => reader data = ", reader_data)
    reader_lock.finish_reading()

    # ==> WRITER process
    print("Set pose_order")
    writer_lock.start_writing()
    writer_data.pose_order.x = 3.0
    writer_data.pose_order.y = 4.0
    writer_data.pose_order.angle = 180.0
    writer_lock.finish_writing()
    writer_lock.start_reading()
    print(" => writer data = ", writer_data)
    writer_lock.finish_reading()

    # ==> READER process
    reader_lock.start_reading()
    print(" => reader data = ", reader_data)
    reader_lock.finish_reading()

    print(f" => pose_current - pose_order = {writer.get_pose_current() - writer.get_pose_order()}")

    # Test for detector_obstacles
    print("\nTest for detector_obstacles")
    reader_detector_obstacles = reader.get_detector_obstacles()
    writer_detector_obstacles = reader.get_detector_obstacles()
    print(" => reader detector_obstacles size = ", reader_detector_obstacles.size())
    writer_detector_obstacles.append(1.0, 2.0)
    writer_detector_obstacles.append(Coords(3.0, 4.0))
    print(" => reader detector_obstacles size = ", reader_detector_obstacles.size())
    print(" => reader detector_obstacles[0] = ", reader_detector_obstacles.get(0))
    print(" => reader detector_obstacles[1] = ", reader_detector_obstacles.get(1))
    writer_detector_obstacles.set(0, 5.0, 6.0)
    writer_detector_obstacles[1] = Coords(7.0, 8.0)
    print(" => reader detector_obstacles[0] = ", reader_detector_obstacles.get(0))
    print(" => reader detector_obstacles[1] = ", reader_detector_obstacles.get(1))
    coords1 = writer_detector_obstacles.get(0)
    coords2 = writer_detector_obstacles[1]
    coords1.x = 9.0
    coords1.y = 10.0
    coords2.x = 11.0
    coords2.y = 12.0
    print(" => reader detector_obstacles[0] = ", reader_detector_obstacles.get(0))
    print(" => reader detector_obstacles[1] = ", reader_detector_obstacles.get(1))

    for i, coords in enumerate(writer_detector_obstacles):
        print(f" => writer iterator on detector_obstacles: coords[{i}] = {coords}")

    for i, coords in enumerate(reader_detector_obstacles):
        print(f" => reader iterator on detector_obstacles: coords[{i}] = {coords}")

    # Test for circle_obstacles
    print("\nTest for circle_obstacles")
    reader_circle_obstacles = reader.get_circle_obstacles()
    writer_circle_obstacles = reader.get_circle_obstacles()
    print(" => reader circle_obstacles size = ", reader_circle_obstacles.size())
    writer_circle_obstacles.append(10, 20, 90, 200, 0.2, 4)
    writer_circle_obstacles.append(
        x=40, y=50, angle=180, radius=300, bounding_box_margin=0.2, bounding_box_points_number=5
    )
    print(" => writer circle_obstacles size = ", len(writer_circle_obstacles))
    for i, obstacle in enumerate(reader_circle_obstacles):
        print(f" => reader iterator on writer_circle_obstacles: obstacle[{i}] = {obstacle}")

    # Test for rectangle_obstacles
    print("\nTest for rectangle_obstacles")
    reader_rectangle_obstacles = reader.get_rectangle_obstacles()
    writer_rectangle_obstacles = reader.get_rectangle_obstacles()
    print(" => reader rectangle_obstacles size = ", reader_rectangle_obstacles.size())
    writer_rectangle_obstacles.append(10, 20, 90, 200, 300, 0.2, 4)
    writer_rectangle_obstacles.append(
        x=40, y=50, angle=180, length_x=250, length_y=350, bounding_box_margin=0.2, bounding_box_points_number=5
    )
    print(" => writer rectangle_obstacles size = ", len(writer_rectangle_obstacles))
    for i, obstacle in enumerate(reader_rectangle_obstacles):
        print(f" => reader iterator on writer_rectangle_obstacles: obstacle[{i}] = {obstacle}")

    # Deep copy test
    copy_list: list[ObstacleCircle] = []
    for obstacle in writer_circle_obstacles:
        copy_list.append(ObstacleCircle(obstacle, deep_copy=True))
    copy_list[0].center.x = 11
    copy_list[0].center.y = 22

    print(" => writer circle_obstacles[0] = ", writer_circle_obstacles[0])
    print(" => copy_list[0] = ", copy_list[0])

    print("\nTest for pose_current_buffer")
    writer_pose_current_buffer.push(1, 2, 90)
    print(reader_pose_current_buffer.last)
    writer_pose_current_buffer.push(1, 3, 90)
    print(reader_pose_current_buffer.last)
    print(reader_pose_current_buffer.get(1))
    try:
        print(reader_pose_current_buffer.get(2))
    except Exception as exc:
        print(exc)
    for i in range(300):
        writer_pose_current_buffer.push(1, i, 90)
    print(reader_pose_current_buffer.last)

    # Control order of shared memory object destruction
    writer_rectangle_obstacles = None
    writer_circle_obstacles = None
    writer_detector_obstacles = None
    writer_lock = None
    writer_pose_current_buffer = None
    writer_pose_current = None
    writer_data = None
    del writer_lock
    del writer

    reader_rectangle_obstacles = None
    reader_circle_obstacles = None
    reader_detector_obstacles = None
    reader_lock = None
    reader_pose_current_buffer = None
    reader_pose_current = None
    reader_data = None
    del reader

    del owner
    print("End.")


if __name__ == "__main__":
    main()
