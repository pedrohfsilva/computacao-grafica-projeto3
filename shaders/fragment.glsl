#version 330 core

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

// --- Aparência base do objeto ---
uniform sampler2D textureSampler;
uniform bool useTexture;
uniform vec4 solidColor;

// --- Material de iluminação individual (requisito 7) ---
uniform float matKd;          // coeficiente de reflexão difusa
uniform float matKs;          // coeficiente de reflexão especular
uniform float matShininess;   // expoente especular
uniform vec3  emission;       // emissão própria (fonte de luz "acesa")
uniform bool  unlit;          // true = cor cheia, sem iluminação (céu)
uniform bool  isExterior;     // objeto pertence ao ambiente externo

uniform vec3 viewPos;         // posição da câmera (para a especular)

// --- Luz ambiente global (liga/desliga e intensidade) ---
uniform bool  ambientOn;
uniform float ambientStrength;

// --- Multiplicadores globais de reflexão (teclado) ---
uniform float globalKd;
uniform float globalKs;

// --- Fontes de luz: 0=carro (spot, externa), 1=lâmpada, 2=celular (internas) ---
#define NUM_LIGHTS 3
struct Light {
    vec3  position;
    vec3  color;
    vec3  direction;     // direção do facho (spotlight)
    float cutoff;        // cosseno do cone interno; < 0 => luz pontual
    float outerCutoff;   // cosseno do cone externo (borda suave)
    float linear;        // atenuação por distância
    float quadratic;
    bool  enabled;
    bool  isExterior;    // escopo: só ilumina objetos do mesmo ambiente
};
uniform Light lights[NUM_LIGHTS];

void main() {
    vec4 base = useTexture ? texture(textureSampler, TexCoord) : solidColor;
    if (base.a < 0.1)            // descarta pixels transparentes
        discard;
    vec3 color = base.rgb;

    // Céu sempre claro: renderizado com cor cheia, sem sombreamento.
    if (unlit) {
        FragColor = vec4(color, base.a);
        return;
    }

    vec3 norm = normalize(Normal);
    vec3 viewDir = normalize(viewPos - FragPos);

    vec3 ambient = ambientOn ? ambientStrength * color : vec3(0.0);
    vec3 diffuse = vec3(0.0);
    vec3 specular = vec3(0.0);

    for (int i = 0; i < NUM_LIGHTS; i++) {
        // A luz só afeta objetos do mesmo ambiente (interno x externo).
        if (!lights[i].enabled || lights[i].isExterior != isExterior)
            continue;

        // Sentido da luz a partir da posição relativa luz/superfície.
        vec3 lightDir = normalize(lights[i].position - FragPos);

        // Reflexão difusa (Lambert).
        float diff = max(dot(norm, lightDir), 0.0);

        // Reflexão especular (Phong).
        vec3 reflectDir = reflect(-lightDir, norm);
        float spec = pow(max(dot(viewDir, reflectDir), 0.0), matShininess);

        // Atenuação por distância.
        float dist = length(lights[i].position - FragPos);
        float att = 1.0 / (1.0 + lights[i].linear * dist + lights[i].quadratic * dist * dist);

        // Facho (spotlight): intensidade cai entre o cone interno e o externo.
        float spot = 1.0;
        if (lights[i].cutoff >= 0.0) {
            float theta = dot(lightDir, normalize(-lights[i].direction));
            spot = clamp((theta - lights[i].outerCutoff) /
                         (lights[i].cutoff - lights[i].outerCutoff), 0.0, 1.0);
        }

        float f = att * spot;
        diffuse  += diff * lights[i].color * color * f;
        specular += spec * lights[i].color * f;
    }

    diffuse  *= matKd * globalKd;
    specular *= matKs * globalKs;

    vec3 result = ambient + diffuse + specular + emission;
    FragColor = vec4(clamp(result, 0.0, 1.0), base.a);
}
