"""Câmera em primeira pessoa controlada pelo teclado."""

import math
import glfw
import glm


class Camera:
    def __init__(self, position):
        self.pos = glm.vec3(position)
        self.world_up = glm.vec3(0, 1, 0)
        self.yaw = -90.0
        self.pitch = 0.0
        self.move_speed = 6.0
        self.turn_speed = 90.0
        self._update_vectors()

    def _update_vectors(self):
        self.front = glm.normalize(glm.vec3(
            math.cos(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch)),
            math.sin(glm.radians(self.pitch)),
            math.sin(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch)),
        ))
        self.right = glm.normalize(glm.cross(self.front, self.world_up))

    def process_input(self, window, dt):
        v = self.move_speed * dt
        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS: self.pos += v * self.front
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS: self.pos -= v * self.front
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS: self.pos -= v * self.right
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS: self.pos += v * self.right
        if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS: self.pos.y += v
        if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS: self.pos.y -= v

        r = self.turn_speed * dt
        if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS: self.yaw -= r
        if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS: self.yaw += r
        if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS: self.pitch += r
        if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS: self.pitch -= r
        self.pitch = max(-89.0, min(89.0, self.pitch))

        # Limites do mundo
        self.pos.x = max(-45.0, min(45.0, self.pos.x))
        self.pos.z = max(-24.0, min(45.0, self.pos.z))
        self.pos.y = max(0.3, min(12.0, self.pos.y))
        self._update_vectors()

    def view_matrix(self):
        return glm.lookAt(self.pos, self.pos + self.front, self.world_up)
