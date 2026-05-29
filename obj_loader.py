"""Carregador de modelos Wavefront (.obj).

Lê vértices (v), coordenadas de textura (vt), normais (vn) e faces (f),
triangulando faces com mais de 3 vértices (fan triangulation). Quando o
modelo não traz normais, elas são calculadas por face (flat shading).
Retorna um array intercalado [x, y, z, nx, ny, nz, u, v] pronto para a GPU.
"""

import numpy as np


def load_obj(path):
    vertices, texcoords, normals = [], [], []
    face_v, face_t, face_n = [], [], []

    with open(path, "r", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                vertices.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("vt "):
                texcoords.append([float(x) for x in line.split()[1:3]])
            elif line.startswith("vn "):
                normals.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("f "):
                vi, ti, ni = [], [], []
                for vert in line.split()[1:]:
                    comp = vert.split("/")
                    vi.append(int(comp[0]) - 1)
                    ti.append(int(comp[1]) - 1 if len(comp) > 1 and comp[1] else 0)
                    ni.append(int(comp[2]) - 1 if len(comp) > 2 and comp[2] else -1)
                for i in range(1, len(vi) - 1):  # triangulação em leque
                    face_v.extend([vi[0], vi[i], vi[i + 1]])
                    face_t.extend([ti[0], ti[i], ti[i + 1]])
                    face_n.extend([ni[0], ni[i], ni[i + 1]])

    vertices = np.array(vertices, dtype=np.float32)
    if not texcoords:                       # modelo sem coordenadas de textura
        texcoords = [[0.0, 0.0]]
        face_t = [0] * len(face_v)
    texcoords = np.array(texcoords, dtype=np.float32)

    face_v = np.array(face_v, dtype=np.int32)
    face_t = np.array(face_t, dtype=np.int32)
    face_n = np.array(face_n, dtype=np.int32)

    positions = vertices[face_v]
    if len(normals) > 0 and (face_n >= 0).all():
        normal_data = np.array(normals, dtype=np.float32)[face_n]
    else:
        normal_data = _flat_normals(positions)

    data = np.hstack((positions, normal_data, texcoords[face_t]))
    return data.astype(np.float32).flatten()


def _flat_normals(positions):
    """Normal por face (flat shading), calculada de forma vetorizada."""
    tris = positions.reshape(-1, 3, 3)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    length = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, length, out=np.zeros_like(n), where=length > 1e-8)
    return np.repeat(n, 3, axis=0).astype(np.float32)
