"""Carro do ambiente externo com dinâmica de direção e faróis."""

import math
import glfw
import glm

_UP = glm.vec3(0, 1, 0)
_MIN_MOVE = 0.2


class Car:
    def __init__(self, game_object):
        self.obj = game_object
        self.pos = glm.vec3(9.0, 0.06, 5.0)
        self.yaw = math.radians(-90.0)
        self.speed = 0.0

        self.accel = 14.0
        self.max_speed = 12.0
        self.max_reverse = 6.0
        self.friction = 8.0
        self.turn_rate = 1.7

        # Geometria do modelo (.obj)
        self.obj.scale = glm.vec3(0.01)
        self.center = glm.vec3(0.0, 11.0, -237.83)
        self.obj.center = self.center
        self._hl_left = glm.vec3(-60.0, 50.0, -45.0)
        self._hl_right = glm.vec3(60.0, 50.0, -45.0)

    @property
    def forward(self):
        return glm.vec3(math.sin(self.yaw), 0.0, math.cos(self.yaw))

    def update(self, window, dt):
        throttle = 0
        if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS:
            throttle += 1
        if (glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or
                glfw.get_key(window, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS):
            throttle -= 1
        steer = 0
        if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
            steer += 1
        if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
            steer -= 1
        self.step(dt, throttle, steer)

    def step(self, dt, throttle, steer):
        if throttle != 0:
            self.speed += throttle * self.accel * dt
        else:
            d = self.friction * dt
            self.speed = 0.0 if abs(self.speed) <= d else self.speed - math.copysign(d, self.speed)
        self.speed = max(-self.max_reverse, min(self.max_speed, self.speed))

        new_yaw = self.yaw
        if abs(self.speed) > _MIN_MOVE:
            new_yaw += steer * self.turn_rate * dt * math.copysign(1.0, self.speed)

        new_fwd = glm.vec3(math.sin(new_yaw), 0.0, math.cos(new_yaw))
        new_pos = self.pos + new_fwd * self.speed * dt

        # Colisão SAT com as paredes externas da sala
        # Sala AABB: centro (0, -8.0), half-extents (8.2, 7.2)
        room_c = glm.vec2(0.0, -8.0)
        room_e = glm.vec2(8.2, 7.2)
        car_c = glm.vec2(new_pos.x, new_pos.z)

        fwd_2d = glm.vec2(new_fwd.x, new_fwd.z)
        right_2d = glm.vec2(fwd_2d.y, -fwd_2d.x)
        car_e = glm.vec2(0.983, 2.378)  # half-width (X local), half-length (Z local)

        axes = [glm.vec2(1, 0), glm.vec2(0, 1), fwd_2d, right_2d]

        collision = True
        for ax in axes:
            r_room = room_e.x * abs(ax.x) + room_e.y * abs(ax.y)
            # A orientação local X (width) e Z (length) em relação ao vetor forward/right
            r_car = car_e.x * abs(glm.dot(right_2d, ax)) + car_e.y * abs(glm.dot(fwd_2d, ax))
            dist = abs(glm.dot(car_c - room_c, ax))
            if dist > r_room + r_car:
                collision = False
                break

        if collision:
            self.speed = 0.0
        else:
            self.pos = new_pos
            self.yaw = new_yaw
            self.obj.pos = glm.vec3(self.pos)
            self.obj.rot = glm.vec3(0.0, self.yaw, 0.0)

    def _world_point(self, raw):
        local = (raw - self.center) * self.obj.scale.x
        right = glm.normalize(glm.cross(_UP, self.forward))
        return self.pos + right * local.x + _UP * local.y + self.forward * local.z

    @property
    def headlight_left(self):
        return self._world_point(self._hl_left)

    @property
    def headlight_right(self):
        return self._world_point(self._hl_right)

    @property
    def light_position(self):
        return (self.headlight_left + self.headlight_right) * 0.5

    @property
    def light_direction(self):
        return glm.normalize(self.forward + glm.vec3(0.0, -0.35, 0.0))
