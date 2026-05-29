"""Carro do ambiente externo: dirige pelo teclado e carrega os faróis.

Dinâmica de carro real:
  - ESPAÇO acelera para frente, SHIFT acelera para trás (ré);
  - sem acelerar, o atrito reduz a velocidade até parar;
  - J/K esterçam, mas só viram com o carro em movimento (a rotação é
    proporcional à velocidade) e, de ré, o sentido se inverte;
  - o carro só anda na direção para onde aponta (não anda de lado).
Os faróis (spotlight) acompanham a posição e a orientação do carro.
"""

import math
import glfw
import glm

_UP = glm.vec3(0, 1, 0)


class Car:
    # Área externa onde o carro pode circular (x, z)
    AREA_X = (-22.0, 22.0)
    AREA_Z = (1.5, 22.0)

    def __init__(self, game_object):
        self.obj = game_object
        self.pos = glm.vec3(9.0, 0.0, 5.0)
        self.yaw = math.radians(-90.0)   # aponta os faróis para a multidão
        self.speed = 0.0

        # Parâmetros de dinâmica
        self.accel = 14.0
        self.max_speed = 12.0
        self.max_reverse = 6.0
        self.friction = 8.0
        self.turn_rate = 1.9

        # Geometria do modelo (coords. cruas do .obj): centro no chão (eixo de
        # rotação) e posição dos dois faróis na dianteira.
        self.obj.scale = glm.vec3(0.01)
        self.center = glm.vec3(0.0, -0.23, -237.83)
        self.obj.center = self.center
        self._hl_left = glm.vec3(-60.0, 50.0, -6.0)
        self._hl_right = glm.vec3(60.0, 50.0, -6.0)

    @property
    def forward(self):
        return glm.vec3(math.sin(self.yaw), 0.0, math.cos(self.yaw))

    def update(self, window, dt):
        """Lê o teclado e aplica a dinâmica."""
        throttle = 0
        if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS:
            throttle += 1                      # frente
        if (glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or
                glfw.get_key(window, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS):
            throttle -= 1                      # ré
        steer = 0
        if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
            steer -= 1                         # esquerda
        if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
            steer += 1                         # direita
        self.step(dt, throttle, steer)

    def step(self, dt, throttle, steer):
        """Integra a dinâmica do carro (separada do teclado p/ testes)."""
        if throttle != 0:
            self.speed += throttle * self.accel * dt
        else:  # atrito: freia até parar
            d = self.friction * dt
            self.speed = 0.0 if abs(self.speed) <= d else self.speed - math.copysign(d, self.speed)
        self.speed = max(-self.max_reverse, min(self.max_speed, self.speed))

        # Esterçamento proporcional à velocidade: parado não vira; de ré inverte.
        self.yaw += steer * self.turn_rate * dt * (self.speed / self.max_speed)

        # Anda apenas na direção para onde aponta (não anda de lado).
        self.pos += self.forward * self.speed * dt
        self.pos.x = max(self.AREA_X[0], min(self.AREA_X[1], self.pos.x))
        self.pos.z = max(self.AREA_Z[0], min(self.AREA_Z[1], self.pos.z))

        self.obj.pos = glm.vec3(self.pos)
        self.obj.rot = glm.vec3(0.0, self.yaw, 0.0)

    def _world_point(self, raw):
        """Converte um ponto em coordenadas cruas do modelo para o mundo."""
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
        # Facho apontando para frente, inclinado para baixo (faróis)
        return glm.normalize(self.forward + glm.vec3(0.0, -0.35, 0.0))
