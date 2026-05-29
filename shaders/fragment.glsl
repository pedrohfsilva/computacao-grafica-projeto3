#version 330 core

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D textureSampler;
uniform bool useTexture;
uniform vec4 solidColor;

// Material próprio de cada objeto (requisito 7: nada vem de .mtl)
uniform float matKd;          // reflexão difusa
uniform float matKs;          // reflexão especular
uniform float matShininess;   // expoente especular
uniform vec3  emission;       // emissão própria (fonte de luz acesa)
// Escopo do objeto na cena
uniform bool  isSky;          // céu: iluminado só pela luz ambiente
uniform bool  isExterior;     // pertence ao ambiente externo
uniform bool  isBoundary;     // porta: fronteira entre os dois ambientes

uniform vec3 viewPos;

// Luz ambiente global
uniform bool  ambientOn;
uniform float ambientStrength;
uniform float doorOpen;

// Multiplicadores globais de reflexão
uniform float globalKd;
uniform float globalKs;

// Fontes de luz: 0=carro (spot, externa), 1=lâmpada, 2=celular (internas)
#define NUM_LIGHTS 3
struct Light {
    vec3  position;
    vec3  color;
    vec3  direction;
    float cutoff;
    float outerCutoff;
    float linear;
    float quadratic;
    bool  enabled;
    bool  isExterior;
};
uniform Light lights[NUM_LIGHTS];

void main() {
    vec4 base = useTexture ? texture(textureSampler, TexCoord) : solidColor;
    if (base.a < 0.1)
        discard;
    vec3 color = base.rgb;

    vec3 norm = normalize(Normal);

    // Ambiente: exterior recebe 100%; sala (fechada) depende da abertura da porta
    float ambientFactor;
    if (isBoundary) {
        // A porta gira de Z+ (fechada) para X+ (aberta). 
        // A face externa aponta para Z+ ou X+, a interna aponta para Z- ou X-.
        ambientFactor = (norm.z > 0.1 || norm.x > 0.1) ? 1.0 : doorOpen;
    } else {
        ambientFactor = isExterior ? 1.0 : doorOpen;
    }
    vec3 ambient = ambientOn ? ambientStrength * ambientFactor * color : vec3(0.0);

    // Céu: só luz ambiente
    if (isSky) {
        FragColor = vec4(ambient, base.a);
        return;
    }

    vec3 viewDir = normalize(viewPos - FragPos);

    vec3 diffuse = vec3(0.0);
    vec3 specular = vec3(0.0);

    for (int i = 0; i < NUM_LIGHTS; i++) {
        // Boundary (porta) recebe luz de ambos os ambientes; demais só do seu escopo
        if (!lights[i].enabled || (!isBoundary && lights[i].isExterior != isExterior))
            continue;

        vec3 lightDir = normalize(lights[i].position - FragPos);

        // Difusa (Lambert): depende do ângulo entre a normal e o sentido da luz
        float diff = max(dot(norm, lightDir), 0.0);

        // Especular (Blinn-Phong): só onde a superfície está voltada para a luz
        vec3 halfwayDir = normalize(lightDir + viewDir);
        float spec = diff > 0.0 ? pow(max(dot(norm, halfwayDir), 0.0), matShininess) : 0.0;

        // Atenuação
        float dist = length(lights[i].position - FragPos);
        float att = 1.0 / (1.0 + lights[i].linear * dist + lights[i].quadratic * dist * dist);

        // Spotlight
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
