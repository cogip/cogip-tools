from pydantic import BaseModel

from cogip.models.models import Vertex
from cogip.utils.argenum import ArgEnum


class TableEnum(ArgEnum):
    """
    Enum for available tables.
    """

    Training = 0
    Game = 1


class Table(BaseModel):
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    def contains(self, point: Vertex, margin: int = 0) -> bool:
        return (
            point.x >= self.x_min + margin
            and point.x <= self.x_max - margin
            and point.y >= self.y_min + margin
            and point.y <= self.y_max - margin
        )


# Full table
table_game = Table(x_min=-1000, x_max=1000, y_min=-1500, y_max=1500)

# Lower-right corner of the full table
table_training = Table(x_min=-1000, x_max=0, y_min=-1500, y_max=0)


tables: dict[TableEnum, Table] = {
    TableEnum.Training: table_training,
    TableEnum.Game: table_game,
}
