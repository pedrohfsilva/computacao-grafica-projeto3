"""Compila, linka e gerencia um programa de shader GLSL (vertex + fragment)."""

import glm
from OpenGL.GL import *


class Shader:
    def __init__(self, vertex_path, fragment_path):
        with open(vertex_path) as f:
            vertex_src = f.read()
        with open(fragment_path) as f:
            fragment_src = f.read()

        vertex = self._compile(vertex_src, GL_VERTEX_SHADER, "VERTEX")
        fragment = self._compile(fragment_src, GL_FRAGMENT_SHADER, "FRAGMENT")

        self.id = glCreateProgram()
        glAttachShader(self.id, vertex)
        glAttachShader(self.id, fragment)
        glLinkProgram(self.id)
        if not glGetProgramiv(self.id, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(self.id).decode())
        glDeleteShader(vertex)
        glDeleteShader(fragment)

        self._cache = {}  # cache de localização dos uniforms

    def use(self):
        glUseProgram(self.id)

    def _loc(self, name):
        if name not in self._cache:
            self._cache[name] = glGetUniformLocation(self.id, name)
        return self._cache[name]

    def set_int(self, name, value):
        glUniform1i(self._loc(name), int(value))

    def set_float(self, name, value):
        glUniform1f(self._loc(name), value)

    def set_vec3(self, name, v):
        glUniform3fv(self._loc(name), 1, glm.value_ptr(v))

    def set_vec4(self, name, v):
        glUniform4fv(self._loc(name), 1, glm.value_ptr(v))

    def set_mat3(self, name, m):
        glUniformMatrix3fv(self._loc(name), 1, GL_FALSE, glm.value_ptr(m))

    def set_mat4(self, name, m):
        glUniformMatrix4fv(self._loc(name), 1, GL_FALSE, glm.value_ptr(m))

    @staticmethod
    def _compile(src, kind, label):
        shader = glCreateShader(kind)
        glShaderSource(shader, src)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            raise RuntimeError(f"Erro ao compilar {label}:\n{glGetShaderInfoLog(shader).decode()}")
        return shader
