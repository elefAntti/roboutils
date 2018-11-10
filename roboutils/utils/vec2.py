from collections import namedtuple
import math


class Vec2(namedtuple('Vec2', ['x', 'y'])):
    __slots__ = ()

    _zero = None

    @classmethod
    def zero(cls) -> 'Vec2':
        if not cls._zero:
            cls._zero = Vec2(0,0)
        return cls._zero

    @property
    def length(self) -> float:
        return math.hypot(self.x, self.y)
    
    @property
    def lengthSq(self) -> float:
        return self.dot(self)

    @property
    def heading(self) -> float:
        return math.atan2(self.y, self.x)

    @staticmethod
    def fromPolar(heading: float, length: float) -> 'Vec2':
        return Vec2(
            x=math.cos(heading) * length,
            y=math.sin(heading) * length)

    def __neg__(self) -> 'Vec2':
        return Vec2(-self.x, -self.y)

    def __add__(self, other: 'Vec2') -> 'Vec2': # type: ignore
        return Vec2(
            x=self.x + other.x,
            y=self.y + other.y)

    def __sub__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(
            x=self.x - other.x,
            y=self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vec2':
        if type(scalar) != float and type(scalar) != int:
            raise TypeError("Can only multiply vector with scalars")
        return Vec2(
            x=self.x*scalar,
            y=self.y*scalar)

    def __rmul__(self, scalar:float) -> 'Vec2':
        return self * scalar

    def __truediv__(self, scalar:float) -> 'Vec2':
        if type(scalar) != float and type(scalar) != int:
            raise TypeError("Can only divide vector with scalars")
        return Vec2(
            x=self.x/scalar,
            y=self.y/scalar)

    def __rdiv__(self, scalar:float) -> 'Vec2':
        return self / scalar

    def dot(self, other:'Vec2') -> float:
        return self.x * other.x + self.y * other.y

    def rotate(self, angle:float) -> 'Vec2':
        s = math.sin(angle)
        c = math.cos(angle)
        return Vec2(
            x=self.x * c - self.y * s,
            y=self.x * s + self.y * c)

    def normalized(self) -> 'Vec2':
        return self / self.length

    def angleBetween(self, other:'Vec2') -> float:
        return math.acos(self.normalized().dot(other.normalized()))

    def projectionOn(self, other:'Vec2') -> float:
        return self.dot(other.normalized())
    
    def distance(self, other:'Vec2') -> float:
        return (self - other).length

    def normal(self):
        return Vec2(
            x = -self.y,
            y = self.x)

class Transform(namedtuple('Transform', ['heading', 'offset'])):
    __slots__ = ()

    _identity = None

    @classmethod
    def identity(cls) -> 'Transform':
        if not cls._identity:
            cls._identity=Transform(0, Vec2.zero())
        return cls._identity

    @staticmethod
    def rotation(angle) -> 'Transform':
        return Transform(heading = angle, offset = Vec2.zero())
    
    @staticmethod
    def translation(vector) -> 'Transform':
        return Transform(heading = 0, offset = vector)

    @property
    def x(self) -> float:
        return self.offset.x

    @property
    def y(self) -> float:
        return self.offset.y

    def applyTo(self, vector: Vec2) -> Vec2:
        return vector.rotate(self.heading) + self.offset

    def after(self, other:'Transform') -> 'Transform':
        return Transform( \
            heading = self.heading + other.heading, \
            offset = self.applyTo(other.offset))

    def inverse(self) -> 'Transform':
        return Transform.rotation(-self.heading)\
            .after(Transform.translation(-self.offset))