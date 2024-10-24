# Corner cases

### 1. **Start or Finish Pose Inside an Obstacle**
If the start or finish position is inside an obstacle, the algorithm should handle this case appropriately to avoid invalid paths.
In case it is the finish pose, the robot cannot reach the point, so return a failure to build the avoidance graph.
If it is the start pose, find the nearest point of the current pose and consider it as the starting point.

```cpp
if (obstacle.get().is_point_inside(_finishPose)) {
    std::cerr << "Finish pose inside obstacle !" << std::endl;
    return false;
}
if (obstacle.get().is_point_inside(_startPose)) {
    _startPose = obstacle.get().nearest_point(_startPose);
}
```

### 2. **Obstacle Center Outside Borders**
When an obstacle is positioned outside the defined borders, it should not be considered for avoidance.

```cpp
if (!_borders.is_point_inside(obstacle.center())) {
    continue;
}
```

### 3. **Segment Crossing Obstacles**
When building the avoidance graph, if a segment between two valid points crosses an obstacle, those points should not be connected.

```cpp
if (obstacle.get().is_segment_crossing(_validPoints[p], _validPoints[p2])) {
    collide = true;
    break;
}
```

### 4. **Dynamic Obstacles During Path Planning**
If dynamic obstacles are present, the algorithm should recompute only if the start point and stop point segment crosses at least one obstacle.
Otherwise it means that the robot can still follow previous avoidance path without recomputing a new path.
This has to be done as the robot for now is slowing down on each point. So recompute each time avoidance with slight modifications will make it "lag".


```cpp
for (auto obstacle : _dynamicObstacles) {
    if (!_borders.is_point_inside(obstacle.get().center())) {
        continue;
    }
    if (obstacle.get().is_segment_crossing(start, stop)) {
        return true;
    }
}
return false;
```

### 5. **Invalid Points After Validation**
If a possible point is determined to be inside another obstacle or outside borders, it should not be added to the valid points list.

```cpp
for (auto &point: obstacle) {
    if (!_borders.is_point_inside(point)) {
        continue;
    }
    if (is_point_in_obstacles(point, nullptr)) {
        continue;
    }
    /* Found a valid point */
    _validPoints[_validPointsCount++] = { point.x(), point.y() };
}
```

### 6. **No Reachable Neighbors**
If the starting point has no reachable neighbors to reach, the algorithm should return an error as there is no possible path.

```cpp
if (_graph[v] == 0) {
    _isAvoidanceComputed = false;
    return false;
}
```

### 7. **Overlapping Obstacles**
If two obstacles overlap, the obstacle which has its center inside another obstacle is ignored.

```cpp
if (is_point_in_obstacles(obstacle.center(), &obstacle)) {
    continue;
}
```

