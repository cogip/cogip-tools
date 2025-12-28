import itertools
import math
from dataclasses import dataclass

from cogip import models


@dataclass
class CrateGroup:
    """
    Represents a group of 4 aligned crates.
    """

    pose: models.Pose  # Center pose of the group (in robot frame usually)
    crates: list[models.Pose]  # List of crate poses in the group
    crate_ids: list[int]  # List of crate IDs, sorted by position (Y axis in group frame)
    bad_crate_count: int  # Number of bad crates in the group (to maximize)


class CrateAnalyzer:
    """
    Analyzes raw crate positions to find valid groups of 4 aligned crates.
    """

    def __init__(self, good_crate_id: int, bad_crate_id: int):
        self.good_crate_id = good_crate_id
        self.bad_crate_id = bad_crate_id
        # Tolerances
        self.max_angle_diff = 10  # degrees
        self.max_x_diff = 20  # mm (alignment along long axis)
        self.max_y_diff = 20  # mm (deviation from expected spacing)
        self.expected_y_offsets = [-75, -25, 25, 75]

    def find_groups(self, crates_found: list[tuple[int, models.Pose]]) -> list[CrateGroup]:
        """
        Analyze the found crates to find valid groups of 4 crates.
        Returns a list of CrateGroup sorted by score (bad_crate_count descending).
        """
        valid_groups = []
        if len(crates_found) < 4:
            return valid_groups

        for combination in itertools.combinations(crates_found, 4):
            # combination is a tuple of 4 (id, pose)
            poses = [c[1] for c in combination]
            ids = [c[0] for c in combination]

            # 1. Check orientation consistency
            angles = [p.O for p in poses]

            # Average angle (doubling angles to handle 0/180 ambiguity)
            avg_sin = sum(math.sin(math.radians(2 * a)) for a in angles) / 4
            avg_cos = sum(math.cos(math.radians(2 * a)) for a in angles) / 4
            avg_angle = math.degrees(math.atan2(avg_sin, avg_cos)) / 2

            # Check deviation from average
            valid_angles = True
            for a in angles:
                diff = a - avg_angle
                # Normalize diff to [-90, 90]
                while diff > 90:
                    diff -= 180
                while diff < -90:
                    diff += 180
                if abs(diff) > self.max_angle_diff:
                    valid_angles = False
                    break
            if not valid_angles:
                continue

            # 2. Transform to group frame (centered at centroid, aligned with avg_angle)
            centroid_x = sum(p.x for p in poses) / 4
            centroid_y = sum(p.y for p in poses) / 4

            # Rotation matrix to transform FROM robot frame TO group frame
            # We want to project points onto the group's local axes.
            # Local X axis direction (long axis of crates): (cos(avg), sin(avg))
            # Local Y axis direction (stacking direction): (-sin(avg), cos(avg))

            rad = math.radians(avg_angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)

            local_coords = []
            for i in range(4):
                dx = poses[i].x - centroid_x
                dy = poses[i].y - centroid_y

                # Project onto local X (long axis)
                lx = dx * cos_a + dy * sin_a
                # Project onto local Y (short axis / stacking direction)
                ly = -dx * sin_a + dy * cos_a

                local_coords.append((lx, ly, ids[i], poses[i]))

            # 3. Check X alignment (should be close to 0)
            if any(abs(lc[0]) > self.max_x_diff for lc in local_coords):
                continue

            # 4. Check Y spacing
            # Sort by local Y
            local_coords.sort(key=lambda x: x[1])

            # Check against expected offsets [-75, -25, 25, 75]
            valid_spacing = True
            for i in range(4):
                if abs(local_coords[i][1] - self.expected_y_offsets[i]) > self.max_y_diff:
                    valid_spacing = False
                    break

            if valid_spacing:
                # Found a valid group
                crates = [lc[3] for lc in local_coords]
                sorted_ids = [lc[2] for lc in local_coords]
                group_pose = models.Pose(x=centroid_x, y=centroid_y, O=avg_angle)

                # Calculate score (number of bad crates)
                bad_count = sum(1 for cid in sorted_ids if cid == self.bad_crate_id)

                valid_groups.append(
                    CrateGroup(
                        pose=group_pose,
                        crates=crates,
                        crate_ids=sorted_ids,
                        bad_crate_count=bad_count,
                    )
                )

        # Sort by bad_crate_count descending
        valid_groups.sort(key=lambda g: g.bad_crate_count, reverse=True)
        return valid_groups
