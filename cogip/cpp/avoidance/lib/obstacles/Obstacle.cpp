#include "obstacles/Obstacle.hpp"

// System includes
#include <cmath>

// Project includes
#include "trigonometry.h"

namespace cogip {

namespace obstacles {

Obstacle::Obstacle(
    const cogip_defs::Pose &center, double radius,
    double bounding_box_margin):
        center_(center), radius_(radius),
        bounding_box_margin_(bounding_box_margin),
        enabled_(true)
{
}

void Obstacle::set_center(cogip_defs::Pose &center)
{
    center_ = center;
}

} // namespace obstacles

} // namespace cogip
