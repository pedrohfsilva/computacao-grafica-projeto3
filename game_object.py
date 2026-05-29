"""Objeto da cena: malha (VAO/VBO), aparência (textura ou cor) e material."""

import ctypes
import glm
import numpy as np
from OpenGL.GL import *
from PIL import Image

import obj_loader

_STRIDE = 8 * 4  # 8 floats por vértice: posição(3) + normal(3) + uv(2)


def load_texture(path, clamp=False, flip_y=True):
    """Carrega uma imagem como textura 2D e devolve o id (0 em caso de falha)."""
    try:
        img = Image.open(path).convert("RGBA")
        if flip_y:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        data = np.frombuffer(img.tobytes(), np.uint8)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        wrap = GL_CLAMP_TO_EDGE if clamp else GL_REPEAT
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(GL_TEXTURE_2D)
        return tex
    except Exception as e:
        print(f"Falha ao carregar textura {path}: {e}")
        return 0


class GameObject:
    def __init__(self, obj_path, texture=None, color=None,
                 exterior=False, clamp_tex=False, flip_y=True):
        data = obj_loader.load_obj(obj_path)
        self.vertex_count = len(data) // 8
        self.texture = load_texture(texture, clamp_tex, flip_y) if texture else 0
        self.color = color if color is not None else glm.vec4(1.0)

        self.vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, _STRIDE, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, _STRIDE, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, _STRIDE, ctypes.c_void_p(24))
        glEnableVertexAttribArray(2)
        glBindVertexArray(0)

        # Transformação
        self.pos = glm.vec3(0.0)
        self.rot = glm.vec3(0.0)      # ângulos de Euler (radianos)
        self.scale = glm.vec3(1.0)
        self.center = glm.vec3(0.0)   # ponto do modelo posto em 'pos' e eixo de rotação

        # Material de iluminação próprio (requisito 7)
        self.kd = 0.8
        self.ks = 0.3
        self.shininess = 32.0
        self.exterior = exterior
        self.emission = glm.vec3(0.0)
        self.unlit = False

    def model_matrix(self):
        m = glm.translate(glm.mat4(1.0), self.pos)
        m = glm.rotate(m, self.rot.y, glm.vec3(0, 1, 0))
        m = glm.rotate(m, self.rot.x, glm.vec3(1, 0, 0))
        m = glm.rotate(m, self.rot.z, glm.vec3(0, 0, 1))
        m = glm.scale(m, self.scale)
        m = glm.translate(m, -self.center)
        return m

    def draw(self, shader):
        if self.vertex_count == 0:
            return
        model = self.model_matrix()
        shader.set_mat4("model", model)
        shader.set_mat3("normalMatrix", glm.transpose(glm.inverse(glm.mat3(model))))
        shader.set_float("matKd", self.kd)
        shader.set_float("matKs", self.ks)
        shader.set_float("matShininess", self.shininess)
        shader.set_vec3("emission", self.emission)
        shader.set_int("unlit", self.unlit)
        shader.set_int("isExterior", self.exterior)

        if self.texture:
            shader.set_int("useTexture", True)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture)
            shader.set_int("textureSampler", 0)
        else:
            shader.set_int("useTexture", False)
            shader.set_vec4("solidColor", self.color)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        glBindVertexArray(0)
