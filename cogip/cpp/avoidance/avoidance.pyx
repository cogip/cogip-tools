# libavoidance.pyx

from libcpp.vector cimport vector
from libcpp cimport bool
from cython.operator cimport dereference as deref

# External C++ Classes and Functions
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

cdef extern from "cogip_defs/Polygon.hpp" namespace "cogip::cogip_defs":
    cdef cppclass Polygon(vector[Coords]):
        Polygon()
        Polygon(const Polygon&)
        int point_index(const Coords& p) const

cdef extern from "avoidance/Avoidance.hpp" namespace "cogip::avoidance":
    cdef cppclass Avoidance:
        Avoidance(const ObstaclePolygon& borders)
        size_t get_path_size() const
        Coords get_path_pose(unsigned char index) const
        void add_dynamic_obstacle(Obstacle& obstacle)
        void remove_dynamic_obstacle(Obstacle& obstacle)
        void clear_dynamic_obstacles()
        bool avoidance(const Coords& start, const Coords& finish)
        bool check_recompute(const Coords& start, const Coords& finish) const

cdef extern from "obstacles/Obstacle.hpp" namespace "cogip::obstacles":
    cdef cppclass Obstacle(Polygon):
        Obstacle()  # Constructor
        bool is_point_inside(const Coords& p) const
        const Polygon& bounding_box() const

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
        ObstacleCircle(Pose& center, double radius, double bb_margin, unsigned int bb_points_number)

# Wrapping Pose class for Python
cdef class CppCoords:
    cdef Coords* c_coords

    def __cinit__(self, double x, double y):
        """
        Initialize a Pose object.
        """
        self.c_coords = new Coords(x, y)

    @property
    def x(self):
        return self.c_coords.x()

    @property
    def y(self):
        return self.c_coords.y()

    def __dealloc__(self):
        """
        Clean up memory for the Pose object.
        """
        del self.c_coords

cdef class CppPose:
    cdef Pose* c_pose

    def __cinit__(self, double x=0.0, double y=0.0, double O=0.0):
        """
        Initialize a Pose object.
        """
        self.c_pose = new Pose(x, y, O)

    @property
    def x(self):
        return self.c_pose.x()

    @property
    def y(self):
        return self.c_pose.y()

    @property
    def O(self):
        return self.c_pose.O()

    def __dealloc__(self):
        """
        Clean up memory for the Pose object.
        """
        del self.c_pose

cdef class CppPolygon:
    cdef Polygon* c_polygon  # Pointeur vers l'objet C++ Polygon
    cdef unsigned int _index

    def __cinit__(self):
        self.c_polygon = new Polygon()

    def __dealloc__(self):
        del self.c_polygon

    def __iter__(self):
        """Initialize the iterator and return self."""
        self._index = 0
        return self

    def __next__(self) -> Coords:
        """Return the next element in the Polygon."""
        cdef Coords p
        cdef CppCoords cpp_coords
        if self._index < self.c_polygon.size():
            p = self.c_polygon.at(self._index)
            self._index += 1
            cpp_coords = CppCoords(p.x(), p.y())
            return cpp_coords
        else:
            raise StopIteration()

    def point_index(self, x: float, y: float) -> int:
        cdef Coords p = Coords(x, y)
        return self.c_polygon.point_index(p)

# Wrapping Obstacle base class
cdef class CppObstacle:
    cdef Obstacle* c_obstacle

    def __dealloc__(self):
        """
        Clean up memory for the Obstacle object.
        """
        del self.c_obstacle

    def contains(self, double x, double y):
        return self.c_obstacle.is_point_inside(Coords(x, y))

    def bounding_box(self):
        cdef CppPolygon cpp_box = CppPolygon()
        cpp_box.c_polygon = new Polygon(self.c_obstacle.bounding_box())
        return cpp_box

# Wrapping ObstacleRectangle for Python
cdef class CppObstacleRectangle(CppObstacle):
    cdef ObstacleRectangle* c_obstacle_rectangle

    def __cinit__(self, double x, double y, double angle, double length_x, double length_y):
        """
        Initialize an ObstacleRectangle object.
        """
        self.c_obstacle_rectangle = new ObstacleRectangle(Pose(x, y, angle), length_x, length_y)
        self.c_obstacle = self.c_obstacle_rectangle

# Wrapping ObstaclePolygon for Python
cdef class CppObstaclePolygon(CppObstacle):
    cdef ObstaclePolygon* c_obstacle_polygon

    def __cinit__(self, list[tuple[float, float]] points):
        """
        Initialize an ObstaclePolygon object with a list of points.
        """
        cdef vector[Coords] polygon_points
        for point in points:
            polygon_points.push_back(Coords(point[0], point[1]))
        self.c_obstacle_polygon = new ObstaclePolygon(polygon_points)
        self.c_obstacle = self.c_obstacle_polygon

# Wrapping ObstacleCircle for Python
cdef class CppObstacleCircle(CppObstacle):
    cdef ObstacleCircle* c_obstacle_circle

    def __cinit__(self, double x, double y, double angle, double radius, double bb_margin, int bb_points_number):
        """
        Initialize an ObstacleCircle object.
        """
        self.c_obstacle_circle = new ObstacleCircle(Pose(x, y, angle), radius, bb_margin, bb_points_number)
        self.c_obstacle = self.c_obstacle_circle

# Wrapping Avoidance class for Python
cdef class CppAvoidance:
    cdef Avoidance* c_avoidance

    def __cinit__(self, CppObstaclePolygon borders):
        """
        Initialize an Avoidance object with the area's borders.
        """
        self.c_avoidance = new Avoidance(deref(borders.c_obstacle_polygon))

    def __dealloc__(self):
        """
        Clean up memory for the Avoidance object.
        """
        del self.c_avoidance

    def get_path_size(self):
        """
        Return the size of the computed avoidance path.
        """
        return self.c_avoidance.get_path_size()

    def get_path_pose(self, unsigned int index):
        """
        Return the pose at the specified index in the computed avoidance path.
        """
        cdef Coords pose = self.c_avoidance.get_path_pose(index)
        return CppPose(pose.x(), pose.y(), 0)

    def add_dynamic_obstacle(self, CppObstacle obstacle):
        """
        Add a dynamic obstacle to the avoidance system.
        """
        self.c_avoidance.add_dynamic_obstacle(deref(obstacle.c_obstacle))

    def remove_dynamic_obstacle(self, CppObstacle obstacle):
        """
        Remove a dynamic obstacle from the avoidance system.
        """
        self.c_avoidance.remove_dynamic_obstacle(deref(obstacle.c_obstacle))

    def clear_dynamic_obstacles(self):
        """
        Clear all dynamic obstacles from the avoidance system.
        """
        self.c_avoidance.clear_dynamic_obstacles()

    def avoidance(self, double start_x, double start_y, double finish_x, double finish_y):
        """
        Compute a path from the start to the finish point considering obstacles.
        """
        cdef Coords start = Coords(start_x, start_y)
        cdef Coords finish = Coords(finish_x, finish_y)
        return self.c_avoidance.avoidance(start, finish)

    def check_recompute(self, double start_x, double start_y, double finish_x, double finish_y):
        """
        Check if a recomputation of the avoidance path is necessary.
        """
        cdef Coords start = Coords(start_x, start_y)
        cdef Coords finish = Coords(finish_x, finish_y)
        return self.c_avoidance.check_recompute(start, finish)
