import ezdxf
from ..utils.vec2 import Vec2
from .world import World, Wall, Line

def fromCadFile(filename: str) -> World:
    walls = []
    lines = []
    drawing = ezdxf.readfile("map.dxf")
    model = drawing.modelspace()
    for entity in model.query('LINE'):
        if entity.dxf.layer == "Walls":
            walls.append(Wall(Vec2(*entity.dxf.start), Vec2(*entity.dxf.end)))
        if entity.dxf.layer == "Lines":
            lines.append(Line([Vec2(*entity.dxf.start), Vec2(*entity.dxf.end)], width=0.10))
    return World(lines=lines, walls=walls)

def fromHardCodedValues() -> World:
    return World(
        lines = [ 
            Line([
                Vec2(-0.7, 0),
                Vec2(0,0),
                Vec2(0.0, 0.7),
                Vec2(0.7, 0.7),
                Vec2(0.6, -0.7),
                Vec2(-0.8, -0.9)],
            width=0.10)],
        walls=[])
