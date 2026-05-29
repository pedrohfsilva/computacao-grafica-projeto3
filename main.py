"""
Projeto 3 — Iluminação (ambiente, difusa e especular)
Computação Gráfica (SCC0250) — ICMC/USP

Cena: sala de aula durante greve universitária, com dois ambientes.
  - Interno: professor, alunos e mesas. Luzes: lâmpada do teto e celular.
  - Externo: grevistas, guarda, caixa de som e carro com faróis.
Controles completos no README.md.
"""

import os
import glfw
from OpenGL.GL import *
import glm

from shader import Shader
from game_object import GameObject
from camera import Camera
from car import Car

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIDTH, HEIGHT = 1280, 720


def model(*parts):
    return os.path.join(BASE_DIR, "modelos", *parts)


# ── Estado da cena ──────────────────────────────────────────────────

class State:
    def __init__(self):
        self.car_light = True
        self.lamp_light = True
        self.phone_light = True
        self.ambient_on = True
        self.ambient = 0.5
        self.diffuse = 1.0
        self.specular = 1.0
        self.hat_scale = 1.0
        self.prof_x = 0.0
        self.door_angle = 0.0
        self.wireframe = False


def make_key_callback(state):
    def callback(window, key, _scancode, action, _mods):
        if action != glfw.PRESS:
            return
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)
        elif key == glfw.KEY_Z:
            state.wireframe = not state.wireframe
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if state.wireframe else GL_FILL)
        elif key == glfw.KEY_F:
            state.car_light = not state.car_light
        elif key == glfw.KEY_T:
            state.lamp_light = not state.lamp_light
        elif key == glfw.KEY_C:
            state.phone_light = not state.phone_light
        elif key == glfw.KEY_B:
            state.ambient_on = not state.ambient_on
    return callback


def scene_input(window, state, dt):
    def held(k):
        return glfw.get_key(window, k) == glfw.PRESS

    if held(glfw.KEY_1): state.hat_scale = max(0.2, state.hat_scale - 0.8 * dt)
    if held(glfw.KEY_2): state.hat_scale = min(4.0, state.hat_scale + 0.8 * dt)
    if held(glfw.KEY_3): state.prof_x = max(-7.0, state.prof_x - 3.0 * dt)
    if held(glfw.KEY_4): state.prof_x = min(7.0, state.prof_x + 3.0 * dt)
    if held(glfw.KEY_5): state.door_angle = max(0.0, state.door_angle - 1.5 * dt)
    if held(glfw.KEY_6): state.door_angle = min(1.5708, state.door_angle + 1.5 * dt)

    adj = 0.6 * dt
    if held(glfw.KEY_U): state.ambient = max(0.0, state.ambient - adj)
    if held(glfw.KEY_I): state.ambient = min(1.0, state.ambient + adj)
    if held(glfw.KEY_O): state.diffuse = max(0.0, state.diffuse - adj)
    if held(glfw.KEY_P): state.diffuse = min(3.0, state.diffuse + adj)
    if held(glfw.KEY_N): state.specular = max(0.0, state.specular - adj)
    if held(glfw.KEY_M): state.specular = min(3.0, state.specular + adj)


# ── Luzes ───────────────────────────────────────────────────────────

def set_light(shader, i, position, color, enabled, exterior,
              direction=glm.vec3(0, -1, 0), cutoff=-1.0, outer=-1.0,
              linear=0.05, quadratic=0.008):
    p = f"lights[{i}]."
    shader.set_vec3(p + "position", position)
    shader.set_vec3(p + "color", color)
    shader.set_vec3(p + "direction", direction)
    shader.set_float(p + "cutoff", cutoff)
    shader.set_float(p + "outerCutoff", outer)
    shader.set_float(p + "linear", linear)
    shader.set_float(p + "quadratic", quadratic)
    shader.set_int(p + "enabled", enabled)
    shader.set_int(p + "isExterior", exterior)


# Duas luzes internas com cores diferentes + uma externa
CAR_COLOR = glm.vec3(1.0, 0.96, 0.88)
LAMP_COLOR = glm.vec3(1.0, 0.85, 0.55)
PHONE_COLOR = glm.vec3(0.35, 0.5, 1.0)


# ── Construção da cena ──────────────────────────────────────────────

def build_scene():
    white = glm.vec4(0.85, 0.85, 0.85, 1.0)
    roof = glm.vec4(0.8, 0.8, 0.8, 1.0)
    cube = model("primitivas", "cubo.obj")
    plane = model("primitivas", "plano.obj")
    sphere = model("primitivas", "esfera.obj")

    s = {}

    # Chão interno (com textura ladrilhada)
    s["floor_indoor"] = GameObject(plane, model("chao_interno", "chao_interno.jpg"))
    s["floor_indoor"].pos = glm.vec3(0, 0.0, -8.0)
    s["floor_indoor"].scale = glm.vec3(8.0, 1.0, 7.0)
    s["floor_indoor"].kd, s["floor_indoor"].ks, s["floor_indoor"].shininess = 0.9, 0.08, 16.0
    s["floor_indoor"].tex_scale = 4.0

    # Teto
    s["ceiling"] = GameObject(cube, color=roof)
    s["ceiling"].pos = glm.vec3(0, 5.0, -8.0)
    s["ceiling"].scale = glm.vec3(8.0, 0.1, 7.0)
    s["ceiling"].kd, s["ceiling"].ks, s["ceiling"].shininess = 0.9, 0.05, 8.0
    s["ceiling"].boundary = True

    # Paredes (boundary: recebem iluminação de ambos os ambientes)
    walls = {
        "wall_left":    (glm.vec3(-8.1, 2.5, -8.0), glm.vec3(0.1, 2.5, 7.0)),
        "wall_right":   (glm.vec3(8.1, 2.5, -8.0),  glm.vec3(0.1, 2.5, 7.0)),
        "wall_back":    (glm.vec3(0, 2.5, -15.1),   glm.vec3(8.0, 2.5, 0.1)),
        "wall_front_l": (glm.vec3(-4.35, 2.5, -0.9), glm.vec3(3.65, 2.5, 0.1)),
        "wall_front_r": (glm.vec3(4.35, 2.5, -0.9),  glm.vec3(3.65, 2.5, 0.1)),
        "wall_front_t": (glm.vec3(0.0, 4.0, -0.9),   glm.vec3(0.7, 1.0, 0.1)),
    }
    for name, (pos, scale) in walls.items():
        w = GameObject(cube, color=white)
        w.pos, w.scale = pos, scale
        w.kd, w.ks, w.shininess = 0.9, 0.05, 8.0
        w.boundary = True
        s[name] = w

    # Chão externo (grama, textura ladrilhada)
    s["floor_outdoor"] = GameObject(plane, model("chao_externo", "chao_externo.jpg"), exterior=True)
    s["floor_outdoor"].pos = glm.vec3(0, -0.02, 0.0)
    s["floor_outdoor"].scale = glm.vec3(100.0, 1.0, 100.0)
    s["floor_outdoor"].kd, s["floor_outdoor"].ks, s["floor_outdoor"].shininess = 0.9, 0.0, 4.0
    s["floor_outdoor"].tex_scale = 25.0

    # Céu
    s["skybox"] = GameObject(sphere, model("skybox", "skybox.png"), exterior=True)
    s["skybox"].scale = glm.vec3(150.0)
    s["skybox"].is_sky = True

    # Porta
    door = GameObject(model("porta", "porta.obj"), model("porta", "porta.jpg"))
    door.scale = glm.vec3(0.015)
    door.pos = glm.vec3(-0.682, -0.1, -0.9)
    door.rot = glm.vec3(-1.5708, 0.0, 0.0)
    door.center = glm.vec3(-45.47, 0.0, 0.0)
    door.kd, door.ks, door.shininess = 0.8, 0.2, 16.0
    s["door"] = door

    # Professor e chapéu
    prof = GameObject(model("professor", "professor.obj"), model("professor", "professor.jpg"))
    prof.scale = glm.vec3(0.01)
    prof.pos = glm.vec3(0, 0, -13.0)
    prof.kd, prof.ks, prof.shininess = 0.85, 0.15, 12.0
    s["prof"] = prof

    hat = GameObject(model("chapeu", "chapeu.obj"), model("chapeu", "chapeu.png"))
    hat.kd, hat.ks, hat.shininess = 0.6, 0.3, 24.0
    s["hat"] = hat

    # Mesa (reutilizada para professor e alunos)
    table = GameObject(model("mesa", "mesa.obj"), model("mesa", "mesa.png"))
    table.scale = glm.vec3(2.0)
    table.rot = glm.vec3(0, 1.57, 0)
    table.kd, table.ks, table.shininess = 0.8, 0.2, 16.0
    s["table"] = table

    # Aluno (reutilizado nas carteiras)
    student = GameObject(model("aluno", "aluno.obj"), model("aluno", "aluno.jpg"))
    student.scale = glm.vec3(0.025)
    student.rot = glm.vec3(0, 3.14, 0)
    student.kd, student.ks, student.shininess = 0.85, 0.15, 10.0
    s["student"] = student

    # Cadeira (reutilizada na barricada)
    chair = GameObject(model("cadeira", "cadeira.obj"), model("cadeira", "cadeira.png"))
    chair.scale = glm.vec3(1.2)
    chair.kd, chair.ks, chair.shininess = 0.8, 0.3, 24.0
    s["chair"] = chair

    # Guarda na porta
    guard = GameObject(model("guarda", "guarda.obj"), model("guarda", "guarda.bmp"), exterior=True)
    guard.scale = glm.vec3(0.001)
    guard.pos = glm.vec3(0.3, 0.581, -0.5)
    guard.rot = glm.vec3(-0.4, 2.5, 0.12)
    guard.kd, guard.ks, guard.shininess = 0.85, 0.15, 12.0
    s["guard"] = guard

    # Grevistas
    striker1 = GameObject(model("grevista1", "grevista1.obj"), model("grevista1", "grevista1.bmp"), exterior=True)
    striker1.scale = glm.vec3(0.3)
    striker1.rot = glm.vec3(0, 3.14, 0)
    striker1.kd, striker1.ks, striker1.shininess = 0.85, 0.15, 10.0
    striker2 = GameObject(model("grevista2", "grevista2.obj"), model("grevista2", "grevista2.bmp"), exterior=True)
    striker2.scale = glm.vec3(0.35)
    striker2.rot = glm.vec3(0, 3.14, 0)
    striker2.kd, striker2.ks, striker2.shininess = 0.85, 0.15, 10.0
    s["striker1"], s["striker2"] = striker1, striker2

    # Caixa de som
    speaker = GameObject(model("caixa_som", "caixa_som.obj"), model("caixa_som", "caixa_som.png"), exterior=True)
    speaker.scale = glm.vec3(0.5)
    speaker.rot = glm.vec3(0, 3.14, 0)
    speaker.pos = glm.vec3(-4, -0.1, 5.0)
    speaker.kd, speaker.ks, speaker.shininess = 0.7, 0.4, 32.0
    s["speaker"] = speaker

    # Lâmpada do teto (fonte de luz interna)
    lamp = GameObject(model("lampada", "lampada.obj"), model("lampada", "lampada.png"))
    lamp.scale = glm.vec3(0.5)
    lamp.pos = glm.vec3(0, 4.5, -8.0)
    lamp.kd, lamp.ks, lamp.shininess = 0.6, 0.5, 64.0
    s["lamp"] = lamp

    # Celular sobre a mesa (fonte de luz interna)
    phone = GameObject(model("smartphone", "smartphone.obj"), model("smartphone", "smartphone.png"))
    phone.scale = glm.vec3(0.08)
    phone.pos = glm.vec3(0.3, 0.82, -12.0)
    phone.rot = glm.vec3(-1.5708, 0, 0)
    phone.kd, phone.ks, phone.shininess = 0.5, 0.8, 96.0
    s["phone"] = phone

    # Carro (externo, com faróis)
    car_obj = GameObject(model("carro", "carro.obj"), model("carro", "carro.png"), exterior=True)
    car_obj.kd, car_obj.ks, car_obj.shininess = 0.7, 0.9, 64.0
    s["car"] = car_obj

    # Esferas dos faróis
    for side in ("hl_left", "hl_right"):
        hl = GameObject(sphere, color=glm.vec4(CAR_COLOR, 1.0), exterior=True)
        hl.scale = glm.vec3(0.06)
        s[side] = hl

    return s


# Posições reutilizadas
STUDENT_LAYOUT = [(-4.0, -8.0), (0.0, -8.0), (4.0, -8.0),
                  (-4.0, -4.0), (0.0, -4.0), (4.0, -4.0)]
BARRICADE = [(-0.5, 0.3), (0.5, 0.3), (0.0, 0.8), (-1.0, 0.7), (1.0, 0.7),
             (-0.3, 1.3), (0.7, 1.2), (-0.8, 1.5), (0.3, 1.7)]


# ── Renderização ────────────────────────────────────────────────────

def draw_frame(shader, s, car, camera, state, projection):
    shader.set_mat4("projection", projection)
    shader.set_mat4("view", camera.view_matrix())
    shader.set_vec3("viewPos", camera.pos)
    shader.set_int("ambientOn", state.ambient_on)
    shader.set_float("ambientStrength", state.ambient)
    shader.set_float("globalKd", state.diffuse)
    shader.set_float("globalKs", state.specular)
    shader.set_float("doorOpen", (state.door_angle / 1.5708) * 0.6)

    # Luz 0: faróis do carro (spotlight, externa)
    set_light(shader, 0, car.light_position, CAR_COLOR, state.car_light, True,
              direction=car.light_direction, cutoff=0.94, outer=0.85,
              linear=0.014, quadratic=0.0006)
    # Luz 1: lâmpada do teto (pontual, interna)
    set_light(shader, 1, s["lamp"].pos + glm.vec3(0, -0.35, 0), LAMP_COLOR,
              state.lamp_light, False, linear=0.05, quadratic=0.008)
    # Luz 2: celular (pontual, interna)
    set_light(shader, 2, s["phone"].pos + glm.vec3(0, 0.15, 0), PHONE_COLOR,
              state.phone_light, False, linear=0.35, quadratic=0.15)

    # Emissão das fontes de luz
    s["lamp"].emission = LAMP_COLOR * 0.9 if state.lamp_light else glm.vec3(0.0)
    s["phone"].emission = PHONE_COLOR * 0.8 if state.phone_light else glm.vec3(0.0)
    for side in ("hl_left", "hl_right"):
        s[side].emission = CAR_COLOR if state.car_light else glm.vec3(0.0)

    # Interações do teclado
    s["hat"].scale = glm.vec3(state.hat_scale)
    s["prof"].pos.x = state.prof_x
    s["door"].rot.y = state.door_angle

    # Céu (sem depth test)
    glDisable(GL_DEPTH_TEST)
    s["skybox"].pos = camera.pos + glm.vec3(0, -50.0, 0)
    s["skybox"].draw(shader)
    glEnable(GL_DEPTH_TEST)

    # Estrutura da sala e ambiente externo
    for name in ("floor_indoor", "floor_outdoor", "ceiling", "wall_left",
                 "wall_right", "wall_back", "wall_front_l", "wall_front_r",
                 "wall_front_t", "door"):
        s[name].draw(shader)

    # Professor e chapéu
    s["prof"].draw(shader)
    s["hat"].pos = s["prof"].pos + glm.vec3(0.13, 1.83, -0.05)
    s["hat"].draw(shader)

    # Mesa do professor + celular
    s["table"].pos = glm.vec3(0, 0, -12.0)
    s["table"].draw(shader)
    s["phone"].draw(shader)

    # Carteiras e alunos
    for sx, sz in STUDENT_LAYOUT:
        s["table"].pos = glm.vec3(sx, 0, sz - 0.8)
        s["table"].draw(shader)
        s["student"].pos = glm.vec3(sx, 0.08, sz)
        s["student"].draw(shader)

    # Barricada de cadeiras
    for bx, bz in BARRICADE:
        s["chair"].pos = glm.vec3(bx, -0.2, bz)
        s["chair"].rot = glm.vec3(0, bx * 1.5 + bz * 0.8, 0)
        s["chair"].draw(shader)

    s["guard"].draw(shader)

    # Grevistas
    for obj, pos in [
        (s["striker1"], glm.vec3(-3, 1.38, 3.5)), (s["striker2"], glm.vec3(-1, 0.375, 4.0)),
        (s["striker1"], glm.vec3(1, 1.38, 3.5)),  (s["striker2"], glm.vec3(3, 0.375, 4.5)),
        (s["striker1"], glm.vec3(-2, 1.38, 5.5)), (s["striker2"], glm.vec3(0, 0.375, 5.0)),
        (s["striker1"], glm.vec3(2, 1.38, 6.0)),  (s["striker2"], glm.vec3(-1, 0.375, 6.5)),
    ]:
        obj.pos = pos
        obj.draw(shader)

    s["speaker"].draw(shader)
    s["lamp"].draw(shader)
    s["car"].draw(shader)

    # Faróis acompanham o carro
    s["hl_left"].pos = car.headlight_left
    s["hl_right"].pos = car.headlight_right
    s["hl_left"].draw(shader)
    s["hl_right"].draw(shader)


# ── Main ────────────────────────────────────────────────────────────

def main():
    if not glfw.init():
        return
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(WIDTH, HEIGHT, "Projeto 3 - Iluminacao", None, None)
    if not window:
        glfw.terminate()
        return
    glfw.make_context_current(window)

    glViewport(0, 0, *glfw.get_framebuffer_size(window))
    glfw.set_framebuffer_size_callback(window, lambda win, w, h: glViewport(0, 0, w, h))

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_MULTISAMPLE)

    shader = Shader(os.path.join(BASE_DIR, "shaders", "vertex.glsl"),
                    os.path.join(BASE_DIR, "shaders", "fragment.glsl"))
    shader.use()

    s = build_scene()
    car = Car(s["car"])
    camera = Camera(glm.vec3(0.0, 2.0, 8.0))

    state = State()
    glfw.set_key_callback(window, make_key_callback(state))

    last = glfw.get_time()
    while not glfw.window_should_close(window):
        now = glfw.get_time()
        dt = now - last
        last = now

        glfw.poll_events()
        camera.process_input(window, dt)
        car.update(window, dt)
        scene_input(window, state, dt)

        fb_w, fb_h = glfw.get_framebuffer_size(window)
        if fb_h == 0:
            continue

        glClearColor(0.05, 0.05, 0.06, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        projection = glm.perspective(glm.radians(45.0), fb_w / fb_h, 0.1, 300.0)
        draw_frame(shader, s, car, camera, state, projection)

        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
