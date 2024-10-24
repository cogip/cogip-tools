# libavoidance.pyx

from libcpp.vector cimport vector
from libcpp cimport bool
from cython.operator cimport dereference as deref

cdef extern from "avoidance/Avoidance.hpp" namespace "":
    cdef cppclass Avoidance:
        Avoidance(const ObstaclePolygon& borders)
        size_t getPathSize()
        Coords getPathPose(unsigned char index) const
        void addDynamicObstacle(Obstacle& obstacle)
        void removeDynamicObstacle(Obstacle& obstacle)
        void clearDynamicObstacles()
        bool buildGraph(const Coords& start, const Coords& finish)
        bool checkRecompute(const Coords& start, const Coords& finish) const

cdef extern from "obstacles/Obstacle.hpp" namespace "cogip::obstacles":
    cdef cppclass Obstacle:
        Obstacle()  # Constructor

cdef extern from "obstacles/ObstacleRectangle.hpp" namespace "cogip::obstacles":
    cdef cppclass ObstacleRectangle(Obstacle):
        ObstacleRectangle()  # Default constructor
        ObstacleRectangle(Pose& center, double x, double y)

cdef extern from "obstacles/ObstaclePolygon.hpp" namespace "cogip::obstacles":
    cdef cppclass ObstaclePolygon(Obstacle):
        ObstaclePolygon()  # Default constructor
        ObstaclePolygon(const vector[Coords]& points)

cdef extern from "obstacles/ObstacleCircle.hpp" namespace "cogip::obstacles":
    cdef cppclass ObstacleCircle(Obstacle):
        ObstacleCircle()  # Default constructor
        ObstacleCircle(Pose& center, double radius)

cdef extern from "cogip_defs/Coords.hpp" namespace "cogip::cogip_defs":
    cdef cppclass Coords:
        Coords()
        Coords(double x, double y)
        double x() const
        double y() const

cdef extern from "cogip_defs/Pose.hpp" namespace "cogip::cogip_defs":
    cdef cppclass Pose:
        Pose()
        Pose(double x, double y, double O)
        double x() const
        double y() const
        double O() const

# Wrapping Pose class for Python
cdef class CppPose:
    cdef Pose* c_pose
    cdef double x, y, O

    @property
    def x(self):
        return self.x

    @property
    def y(self):
        return self.y

    @property
    def O(self):
        return self.O

    def __cinit__(self):
        pass

    def __cinit__(self,
                  x: float,
                  y: float,
                  O: float):
        self.c_pose = new Pose(x, y, 0)
        self.x = x
        self.y = y
        self.O = O
        pass

    def __dealloc__(self):
        del self.c_pose

# Wrapping Obstacle class for Python
cdef class CppObstacle:
    cdef Obstacle* c_obstacle
    cdef double x, y, angle

    def __cinit__(self):
        pass

    def __dealloc__(self):
        del self.c_obstacle

# Wrapping ObstacleRectangle for Python
cdef class CppObstacleRectangle(CppObstacle):
    cdef ObstacleRectangle* c_obstacle_rectangle

    def __cinit__(self,
                  x: float,
                  y: float,
                  angle: float,
                  length_x: float,
                  length_y: float):
        """
        Initialize an obstacle rectangle with a list of points (tuples of x, y).
        """
        cdef vector[Coords] rectangle_points
        self.c_obstacle_rectangle = new ObstacleRectangle(
            Pose(x, y, angle),
            length_x,
            length_y)
        self.c_obstacle = self.c_obstacle_rectangle

        # Save coordinates
        self.x = x
        self.y = y
        self.angle = angle

# Wrapping ObstaclePolygon for Python
cdef class CppObstaclePolygon(CppObstacle):
    cdef ObstaclePolygon* c_obstacle_polygon

    def __cinit__(self,
                  points: list[tuple(float, float)]):
        """
        Initialize an obstacle polygon with a list of points (tuples of x, y).
        """
        cdef vector[Coords] polygon_points
        for point in points:
            x, y = point
            polygon_points.push_back(Coords(x, y))
        self.c_obstacle_polygon = new ObstaclePolygon(polygon_points)
        self.c_obstacle = self.c_obstacle_polygon

# Wrapping ObstacleCircle for Python
cdef class CppObstacleCircle(CppObstacle):
    cdef ObstacleCircle* c_obstacle_circle

    def __cinit__(self,
                  x: float,
                  y: float,
                  angle: float,
                  radius: float):
        """
        Initialize an obstacle circle with a center and a Radius.
        """
        self.c_obstacle_circle = new ObstacleCircle(Pose(x, y, angle), radius)
        self.c_obstacle = self.c_obstacle_circle

        # Save coordinates
        self.x = x
        self.y = y
        self.angle = angle

# Wrapping Avoidance class for Python
cdef class CppAvoidance:
    cdef Avoidance* c_avoidance

    def __cinit__(self, CppObstaclePolygon borders):
        """
        Initialize Avoidance object with the borders of the area.
        """
        self.c_avoidance = new Avoidance(deref(borders.c_obstacle_polygon))

    def __dealloc__(self):
        del self.c_avoidance

    def get_path_size(self):
        """
        Get computed avoidance path size including start and stop pose.
        """
        return self.c_avoidance.getPathSize()

    def get_path_pose(self, unsigned int index):
        """
        Get pose in computed avoidance path.
        """
        cdef Coords pose = self.c_avoidance.getPathPose(index)
        return CppPose(pose.x(), pose.y(), 0)

    def add_dynamic_obstacle(self, CppObstacle obstacle):
        """
        Add a dynamic obstacle to the avoidance system.
        """
        self.c_avoidance.addDynamicObstacle(deref(obstacle.c_obstacle))

    def remove_dynamic_obstacle(self, CppObstacle obstacle):
        """
        Remove a dynamic obstacle from the avoidance system.
        """
        self.c_avoidance.removeDynamicObstacle(deref(obstacle.c_obstacle))

    def clear_dynamic_obstacles(self):
        """
        Clear all dynamic obstacles from the avoidance system.
        """
        self.c_avoidance.clearDynamicObstacles()

    def build_graph(self, double start_x, double start_y, double finish_x, double finish_y):
        """
        Build a graph between the start and finish points in the avoidance area.
        """
        cdef Coords start = Coords(start_x, start_y)
        cdef Coords finish = Coords(finish_x, finish_y)
        return self.c_avoidance.buildGraph(start, finish)

    def check_recompute(self, double start_x, double start_y, double finish_x, double finish_y):
        """
        Build a graph between the start and finish points in the avoidance area.
        """
        cdef Coords start = Coords(start_x, start_y)
        cdef Coords finish = Coords(finish_x, finish_y)
        return self.c_avoidance.checkRecompute(start, finish)