# Projeto 3 — Computação Gráfica (SCC0250)

Cena 3D interativa em Python com OpenGL 3.3+ (pipeline moderno, shaders GLSL).
Evolução do Projeto 2 com **iluminação ambiente, difusa e especular** (modelo de Phong).

## Alunos
- Ayrton da Costa Ganem Filho - 14560190
- Pedro Henrique Ferreira Silva - 14677526

## Descrição da Cena

Uma **sala de aula durante uma greve universitária**, com dois ambientes conectados pela porta:

**Ambiente interno — sala de aula**
- Professor (com chapéu) e sua mesa, com um **celular** servindo de luminária.
- Seis alunos sentados em carteiras.
- **Lâmpada** no teto.

**Ambiente externo — greve**
- Oito grevistas, um guarda na porta e uma caixa de som.
- Barricada de cadeiras bloqueando a entrada.
- Um **carro com faróis** que pode ser dirigido pelo teclado.
- Céu (skybox) iluminado pela luz ambiente (fica mais claro ou mais escuro com ela).

## Iluminação

São três fontes de luz, além da luz ambiente global:

| Luz | Tipo | Cor | Ambiente que ilumina |
|-----|------|-----|----------------------|
| Faróis do carro | Spotlight (segue o carro) | Branco quente | Apenas externo |
| Lâmpada do teto | Pontual | Amarelo quente | Apenas interno |
| Celular | Pontual | Azul | Apenas interno |

Como os requisitos são atendidos:

1. **Objeto externo com translação e luz** — o carro translada/gira pelo teclado e
   carrega os faróis (spotlight) que iluminam para a frente; sua luz só afeta objetos externos.
2. **Duas luzes internas de cores diferentes** — lâmpada (amarela) e celular (azul); só afetam o interior.
3. **Interruptores independentes** — cada luz, inclusive a ambiente, liga/desliga separadamente.
4. **Controle da luz ambiente** — incrementa/decrementa em tempo real.
5. **Controle da reflexão difusa** — incrementa/decrementa em tempo real.
6. **Controle da reflexão especular** — incrementa/decrementa em tempo real.
7. **Parâmetros individuais** — cada objeto define seus próprios `kd`, `ks` e brilho no código
   (nenhum parâmetro vem de arquivos `.mtl`).

Detalhes de escopo (no fragment shader):
- Cada luz só ilumina objetos do seu ambiente (a do carro, o externo; lâmpada e celular, o interno).
- O céu recebe apenas a luz ambiente, então clareia ou escurece conforme ela.
- A sala é fechada: o interior **não** recebe a luz ambiente, só as luzes internas. Ao abrir
  a porta, um pouco de ambiente entra (proporcional à abertura).

## Pré-requisitos

- Python 3.x
- Bibliotecas: `PyOpenGL`, `glfw`, `PyGLM`, `numpy`, `Pillow`

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Controles

**Câmera**
| Tecla | Ação |
|-------|------|
| W / A / S / D | Mover |
| Q / E | Descer / subir |
| Setas ← → ↑ ↓ | Olhar ao redor |

**Carro**
| Tecla | Ação |
|-------|------|
| Espaço | Acelerar para frente |
| Shift | Ré (acelerar para trás) |
| J / K | Virar à esquerda / direita (só vira em movimento; de ré, inverte) |

**Interruptores de luz (liga/desliga)**
| Tecla | Luz |
|-------|-----|
| F | Faróis do carro (externa) |
| T | Lâmpada do teto (interna) |
| C | Celular (interna, azul) |
| B | Luz ambiente |

**Intensidade da iluminação**
| Tecla | Ação |
|-------|------|
| U / I | Luz ambiente − / + |
| O / P | Reflexão difusa − / + |
| N / M | Reflexão especular − / + |

**Cena**
| Tecla | Ação |
|-------|------|
| 1 / 2 | Diminuir / aumentar o chapéu |
| 3 / 4 | Mover o professor (esquerda / direita) |
| 5 / 6 | Fechar / abrir a porta |
| Z | Alternar wireframe |
| ESC | Sair |

## Estrutura do projeto

```
Trabalho 3 CG/
├── main.py            # Inicialização, montagem da cena e laço de renderização
├── camera.py          # Câmera em primeira pessoa
├── car.py             # Carro dirigível e seus faróis (spotlight)
├── game_object.py     # Objeto da cena (malha, textura, material) e carga de texturas
├── obj_loader.py      # Leitor de arquivos Wavefront (.obj)
├── shader.py          # Compilação e uso do programa de shaders
├── shaders/
│   ├── vertex.glsl    # Vertex shader (transformações)
│   └── fragment.glsl  # Fragment shader (iluminação de Phong)
├── modelos/           # Modelos .obj e texturas
│   ├── primitivas/    # cubo, plano, esfera
│   ├── chao_interno/  chao_externo/  skybox/
│   ├── aluno/  cadeira/  caixa_som/  carro/  chapeu/
│   ├── grevista1/  grevista2/  guarda/  lampada/  mesa/
│   └── porta/  professor/  smartphone/
├── requirements.txt
└── README.md
```
