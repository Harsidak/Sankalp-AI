import * as THREE from 'three';

const vertexShader = `
precision highp float;

void main() {
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const fragmentShader = `
precision highp float;

uniform float iTime;
uniform vec3  iResolution;
uniform float animationSpeed;

uniform bool enableTop;
uniform bool enableMiddle;
uniform bool enableBottom;

uniform int topLineCount;
uniform int middleLineCount;
uniform int bottomLineCount;

uniform float topLineDistance;
uniform float middleLineDistance;
uniform float bottomLineDistance;

uniform vec3 topWavePosition;
uniform vec3 middleWavePosition;
uniform vec3 bottomWavePosition;

uniform vec2 iMouse;
uniform bool interactive;
uniform float bendRadius;
uniform float bendStrength;
uniform float bendInfluence;

uniform bool parallax;
uniform float parallaxStrength;
uniform vec2 parallaxOffset;

uniform vec3 lineGradient[8];
uniform int lineGradientCount;

const vec3 BLACK = vec3(0.0);
const vec3 PINK  = vec3(233.0, 71.0, 245.0) / 255.0;
const vec3 BLUE  = vec3(47.0,  75.0, 162.0) / 255.0;

mat2 rotate(float r) {
  return mat2(cos(r), sin(r), -sin(r), cos(r));
}

vec3 background_color(vec2 uv) {
  vec3 col = vec3(0.0);

  float y = sin(uv.x - 0.2) * 0.3 - 0.1;
  float m = uv.y - y;

  col += mix(BLUE, BLACK, smoothstep(0.0, 1.0, abs(m)));
  col += mix(PINK, BLACK, smoothstep(0.0, 1.0, abs(m - 0.8)));
  return col * 0.5;
}

vec3 getLineColor(float t, vec3 baseColor) {
  if (lineGradientCount <= 0) {
    return baseColor;
  }

  vec3 gradientColor;
  
  if (lineGradientCount == 1) {
    gradientColor = lineGradient[0];
  } else {
    float clampedT = clamp(t, 0.0, 0.9999);
    float scaled = clampedT * float(lineGradientCount - 1);
    int idx = int(floor(scaled));
    float f = fract(scaled);
    int idx2 = min(idx + 1, lineGradientCount - 1);

    vec3 c1 = lineGradient[idx];
    vec3 c2 = lineGradient[idx2];
    
    gradientColor = mix(c1, c2, f);
  }
  
  return gradientColor * 0.5;
}

  float wave(vec2 uv, float offset, vec2 screenUv, vec2 mouseUv, bool shouldBend) {
  float time = iTime * animationSpeed;

  float x_offset   = offset;
  float x_movement = time * 0.1;
  float amp        = sin(offset + time * 0.2) * 0.3;
  float y          = sin(uv.x + x_offset + x_movement) * amp;

  if (shouldBend) {
    vec2 d = screenUv - mouseUv;
    float influence = exp(-dot(d, d) * bendRadius); // radial falloff around cursor
    float bendOffset = (mouseUv.y - screenUv.y) * influence * bendStrength * bendInfluence;
    y += bendOffset;
  }

  float m = uv.y - y;
  return 0.0175 / max(abs(m) + 0.01, 1e-3) + 0.01;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
  vec2 baseUv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
  baseUv.y *= -1.0;
  
  if (parallax) {
    baseUv += parallaxOffset;
  }

  vec3 col = vec3(0.0);

  vec3 b = lineGradientCount > 0 ? vec3(0.0) : background_color(baseUv);

  vec2 mouseUv = vec2(0.0);
  if (interactive) {
    mouseUv = (2.0 * iMouse - iResolution.xy) / iResolution.y;
    mouseUv.y *= -1.0;
  }
  
  if (enableBottom) {
    for (int i = 0; i < bottomLineCount; ++i) {
      float fi = float(i);
      float t = fi / max(float(bottomLineCount - 1), 1.0);
      vec3 lineCol = getLineColor(t, b);
      
      float angle = bottomWavePosition.z * log(length(baseUv) + 1.0);
      vec2 ruv = baseUv * rotate(angle);
      col += lineCol * wave(
        ruv + vec2(bottomLineDistance * fi + bottomWavePosition.x, bottomWavePosition.y),
        1.5 + 0.2 * fi,
        baseUv,
        mouseUv,
        interactive
      ) * 0.2;
    }
  }

  if (enableMiddle) {
    for (int i = 0; i < middleLineCount; ++i) {
      float fi = float(i);
      float t = fi / max(float(middleLineCount - 1), 1.0);
      vec3 lineCol = getLineColor(t, b);
      
      float angle = middleWavePosition.z * log(length(baseUv) + 1.0);
      vec2 ruv = baseUv * rotate(angle);
      col += lineCol * wave(
        ruv + vec2(middleLineDistance * fi + middleWavePosition.x, middleWavePosition.y),
        2.0 + 0.15 * fi,
        baseUv,
        mouseUv,
        interactive
      );
    }
  }

  if (enableTop) {
    for (int i = 0; i < topLineCount; ++i) {
      float fi = float(i);
      float t = fi / max(float(topLineCount - 1), 1.0);
      vec3 lineCol = getLineColor(t, b);
      
      float angle = topWavePosition.z * log(length(baseUv) + 1.0);
      vec2 ruv = baseUv * rotate(angle);
      ruv.x *= -1.0;
      col += lineCol * wave(
        ruv + vec2(topLineDistance * fi + topWavePosition.x, topWavePosition.y),
        1.0 + 0.2 * fi,
        baseUv,
        mouseUv,
        interactive
      ) * 0.1;
    }
  }

  fragColor = vec4(col, 1.0);
}

void main() {
  vec4 color = vec4(0.0);
  mainImage(color, gl_FragCoord.xy);
  gl_FragColor = color;
}
`;

const MAX_GRADIENT_STOPS = 8;

function hexToVec3(hex) {
  let value = hex.trim();

  if (value.startsWith('#')) {
    value = value.slice(1);
  }

  let r = 255;
  let g = 255;
  let b = 255;

  if (value.length === 3) {
    r = parseInt(value[0] + value[0], 16);
    g = parseInt(value[1] + value[1], 16);
    b = parseInt(value[2] + value[2], 16);
  } else if (value.length === 6) {
    r = parseInt(value.slice(0, 2), 16);
    g = parseInt(value.slice(2, 4), 16);
    b = parseInt(value.slice(4, 6), 16);
  }

  return new THREE.Vector3(r / 255, g / 255, b / 255);
}

export class FloatingLines {
  constructor(container, options = {}) {
    this.container = container;

    // Default options
    this.options = {
      linesGradient: options.linesGradient || [],
      enabledWaves: options.enabledWaves || ['top', 'middle', 'bottom'],
      lineCount: options.lineCount || 6,
      lineDistance: options.lineDistance || 5,
      topWavePosition: options.topWavePosition,
      middleWavePosition: options.middleWavePosition,
      bottomWavePosition: options.bottomWavePosition || { x: 2.0, y: -0.7, rotate: -1 },
      animationSpeed: options.animationSpeed || 1,
      interactive: options.interactive !== undefined ? options.interactive : true,
      bendRadius: options.bendRadius || 5.0,
      bendStrength: options.bendStrength || -0.5,
      mouseDamping: options.mouseDamping || 0.05,
      parallax: options.parallax !== undefined ? options.parallax : true,
      parallaxStrength: options.parallaxStrength || 0.2,
      mixBlendMode: options.mixBlendMode || 'screen'
    };

    this.init();
  }

  init() {
    // State
    this.targetMouse = new THREE.Vector2(-1000, -1000);
    this.currentMouse = new THREE.Vector2(-1000, -1000);
    this.targetInfluence = 0;
    this.currentInfluence = 0;
    this.targetParallax = new THREE.Vector2(0, 0);
    this.currentParallax = new THREE.Vector2(0, 0);

    // Three.js setup
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.camera.position.z = 1;

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.container.appendChild(this.renderer.domElement);

    // Uniforms calculation
    const getLineCount = (waveType) => {
      if (typeof this.options.lineCount === 'number') return this.options.lineCount;
      if (!this.options.enabledWaves.includes(waveType)) return 0;
      const index = this.options.enabledWaves.indexOf(waveType);
      return this.options.lineCount[index] ?? 6;
    };

    const getLineDistance = (waveType) => {
      if (typeof this.options.lineDistance === 'number') return this.options.lineDistance;
      if (!this.options.enabledWaves.includes(waveType)) return 0.1;
      const index = this.options.enabledWaves.indexOf(waveType);
      return this.options.lineDistance[index] ?? 0.1;
    };

    const topLineCount = this.options.enabledWaves.includes('top') ? getLineCount('top') : 0;
    const middleLineCount = this.options.enabledWaves.includes('middle') ? getLineCount('middle') : 0;
    const bottomLineCount = this.options.enabledWaves.includes('bottom') ? getLineCount('bottom') : 0;

    const topLineDistance = this.options.enabledWaves.includes('top') ? getLineDistance('top') * 0.01 : 0.01;
    const middleLineDistance = this.options.enabledWaves.includes('middle') ? getLineDistance('middle') * 0.01 : 0.01;
    const bottomLineDistance = this.options.enabledWaves.includes('bottom') ? getLineDistance('bottom') * 0.01 : 0.01;

    this.uniforms = {
      iTime: { value: 0 },
      iResolution: { value: new THREE.Vector3(1, 1, 1) },
      animationSpeed: { value: this.options.animationSpeed },

      enableTop: { value: this.options.enabledWaves.includes('top') },
      enableMiddle: { value: this.options.enabledWaves.includes('middle') },
      enableBottom: { value: this.options.enabledWaves.includes('bottom') },

      topLineCount: { value: topLineCount },
      middleLineCount: { value: middleLineCount },
      bottomLineCount: { value: bottomLineCount },

      topLineDistance: { value: topLineDistance },
      middleLineDistance: { value: middleLineDistance },
      bottomLineDistance: { value: bottomLineDistance },

      topWavePosition: {
        value: new THREE.Vector3(
          this.options.topWavePosition?.x ?? 10.0,
          this.options.topWavePosition?.y ?? 0.5,
          this.options.topWavePosition?.rotate ?? -0.4
        )
      },
      middleWavePosition: {
        value: new THREE.Vector3(
          this.options.middleWavePosition?.x ?? 5.0,
          this.options.middleWavePosition?.y ?? 0.0,
          this.options.middleWavePosition?.rotate ?? 0.2
        )
      },
      bottomWavePosition: {
        value: new THREE.Vector3(
          this.options.bottomWavePosition?.x ?? 2.0,
          this.options.bottomWavePosition?.y ?? -0.7,
          this.options.bottomWavePosition?.rotate ?? 0.4
        )
      },

      iMouse: { value: new THREE.Vector2(-1000, -1000) },
      interactive: { value: this.options.interactive },
      bendRadius: { value: this.options.bendRadius },
      bendStrength: { value: this.options.bendStrength },
      bendInfluence: { value: 0 },

      parallax: { value: this.options.parallax },
      parallaxStrength: { value: this.options.parallaxStrength },
      parallaxOffset: { value: new THREE.Vector2(0, 0) },

      lineGradient: {
        value: Array.from({ length: MAX_GRADIENT_STOPS }, () => new THREE.Vector3(1, 1, 1))
      },
      lineGradientCount: { value: 0 }
    };

    if (this.options.linesGradient && this.options.linesGradient.length > 0) {
      const stops = this.options.linesGradient.slice(0, MAX_GRADIENT_STOPS);
      this.uniforms.lineGradientCount.value = stops.length;
      stops.forEach((hex, i) => {
        const color = hexToVec3(hex);
        this.uniforms.lineGradient.value[i].set(color.x, color.y, color.z);
      });
    }

    const material = new THREE.ShaderMaterial({
      uniforms: this.uniforms,
      vertexShader,
      fragmentShader
    });

    const geometry = new THREE.PlaneGeometry(2, 2);
    const mesh = new THREE.Mesh(geometry, material);
    this.scene.add(mesh);

    this.clock = new THREE.Clock();

    // Event Listeners
    if (this.options.interactive) {
      this.boundHandlePointerMove = this.handlePointerMove.bind(this);
      // Listen on window to capture cursor even when over content
      window.addEventListener('pointermove', this.boundHandlePointerMove);
      // window.addEventListener('pointerleave', this.boundHandlePointerLeave); // Window leave is tricky, maybe skip
    }

    // Resize
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(this.container);
    this.resize(); // Initial resize

    // Start Loop
    this.animate();
  }

  setSize() {
    const width = this.container.clientWidth || 1;
    const height = this.container.clientHeight || 1;
    this.renderer.setSize(width, height, false);
    this.uniforms.iResolution.value.set(width, height, 1);
  }

  resize() {
    this.setSize();
  }

  handlePointerMove(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const dpr = this.renderer.getPixelRatio();

    this.targetMouse.set(x * dpr, (rect.height - y) * dpr);
    this.targetInfluence = 1.0;

    if (this.options.parallax) {
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const offsetX = (x - centerX) / rect.width;
      const offsetY = -(y - centerY) / rect.height;
      this.targetParallax.set(offsetX * this.options.parallaxStrength, offsetY * this.options.parallaxStrength);
    }
  }

  handlePointerLeave() {
    this.targetInfluence = 0.0;
  }

  animate() {
    this.raf = requestAnimationFrame(() => this.animate());

    this.uniforms.iTime.value = this.clock.getElapsedTime();

    if (this.options.interactive) {
      this.currentMouse.lerp(this.targetMouse, this.options.mouseDamping);
      this.uniforms.iMouse.value.copy(this.currentMouse);

      this.currentInfluence += (this.targetInfluence - this.currentInfluence) * this.options.mouseDamping;
      this.uniforms.bendInfluence.value = this.currentInfluence;
    }

    if (this.options.parallax) {
      this.currentParallax.lerp(this.targetParallax, this.options.mouseDamping);
      this.uniforms.parallaxOffset.value.copy(this.currentParallax);
    }

    this.renderer.render(this.scene, this.camera);
  }

  dispose() {
    cancelAnimationFrame(this.raf);
    this.resizeObserver.disconnect();

    if (this.options.interactive) {
      this.renderer.domElement.removeEventListener('pointermove', this.boundHandlePointerMove);
      this.renderer.domElement.removeEventListener('pointerleave', this.boundHandlePointerLeave);
    }

    this.renderer.dispose();
    this.container.removeChild(this.renderer.domElement);
  }
}
