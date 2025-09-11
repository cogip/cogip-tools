from cogip import models
from cogip.cpp.libraries.avoidance import Avoidance as CppAvoidance
from cogip.cpp.libraries.models import Coords as SharedCoord
from cogip.cpp.libraries.shared_memory import SharedProperties
from cogip.utils.argenum import ArgEnum
from .. import logger


class AvoidanceStrategy(ArgEnum):
    Disabled = 0
    StopAndGo = 1
    AvoidanceCpp = 2


class Avoidance:
    def __init__(self, shared_properties: SharedProperties):
        self.shared_properties = shared_properties
        self.cpp_avoidance = CppAvoidance(f"cogip_{shared_properties.robot_id}")

    def check_recompute(self, pose_current: models.PathPose, goal: models.PathPose) -> bool:
        match self.shared_properties.avoidance_strategy:
            case AvoidanceStrategy.AvoidanceCpp:
                return self.cpp_avoidance.check_recompute(
                    SharedCoord(x=pose_current.x, y=pose_current.y),
                    SharedCoord(x=goal.x, y=goal.y),
                )
            case _:
                return True

    def get_path(
        self,
        pose_current: models.PathPose,
        goal: models.PathPose,
    ) -> list[models.PathPose]:
        match self.shared_properties.avoidance_strategy:
            case AvoidanceStrategy.Disabled:
                path = [pose_current.model_copy(), goal.model_copy()]
            case _:
                path = []
                res = self.cpp_avoidance.avoidance(
                    SharedCoord(pose_current.x, pose_current.y),
                    SharedCoord(goal.x, goal.y),
                )
                logger.debug(f"Avoidance: build graph success = {res}")
                if res:
                    for i in range(self.cpp_avoidance.get_path_size()):
                        shared_pose = self.cpp_avoidance.get_path_pose(i)
                        pose = models.PathPose(
                            x=shared_pose.x,
                            y=shared_pose.y,
                            bypass_final_orientation=True,
                            is_intermediate=True,
                        )
                        path.append(pose)

                    # Remove duplicates
                    path = [p for i, p in enumerate(path) if (p.x, p.y) not in {(p2.x, p2.y) for p2 in path[:i]}]

                    # Append final pose order
                    path.append(goal.model_copy())
                else:
                    path = []
                if self.shared_properties.avoidance_strategy == AvoidanceStrategy.StopAndGo and len(path) > 2:
                    path = []
        return path
