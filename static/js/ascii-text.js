import * as THREE from './three.module.js';

/**
 * Three.js / Shader Logic Ported from React-Bits ASCIIText
 */

const vertexShader = `
varying vec2 vUv;
uniform float uTime;
uniform float mouse;
uniform float uEnableWaves;

void main() {
    vUv = uv;
    float time = uTime * 5.;

    float waveFactor = uEnableWaves;

    vec3 transformed = position;

    transformed.x += sin(time + position.y) * 0.5 * waveFactor;
    transformed.y += cos(time + position.z) * 0.15 * waveFactor;
    transformed.z += sin(time + position.x) * waveFactor;

    gl_Position = projectionMatrix * modelViewMatrix * vec4(transformed, 1.0);
}
`;

const fragmentShader = `
varying vec2 vUv;
uniform float mouse;
uniform float uTime;
uniform sampler2D uTexture;

void main() {
    float time = uTime;
    vec2 pos = vUv;
    
    float move = sin(time + mouse) * 0.01;
    float r = texture2D(uTexture, pos + cos(time * 2. - time + pos.x) * .01).r;
    float g = texture2D(uTexture, pos + tan(time * .5 + pos.x - time) * .01).g;
    float b = texture2D(uTexture, pos - cos(time * 2. + time + pos.y) * .01).b;
    float a = texture2D(uTexture, pos).a;
    gl_FragColor = vec4(r, g, b, a);
}
`;

const PX_RATIO = window.devicePixelRatio || 1;

class AsciiFilter {
    constructor(renderer, { fontSize, fontFamily, charset, invert } = {}) {
        this.renderer = renderer;
        this.domElement = document.createElement('div');
        Object.assign(this.domElement.style, {
            position: 'absolute', top: '0', left: '0', width: '100%', height: '100%', pointerEvents: 'none'
        });

        this.pre = document.createElement('pre');
        this.domElement.appendChild(this.pre);

        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d');
        // this.domElement.appendChild(this.canvas); // Debug canvas if needed

        this.deg = 0;
        this.invert = invert ?? true;
        this.fontSize = fontSize ?? 12;
        this.fontFamily = fontFamily ?? "'Courier New', monospace";
        this.charset = charset ?? ' .\'`^",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$';

        this.context.imageSmoothingEnabled = false;

        this.mouse = { x: 0, y: 0 };
        this.center = { x: 0, y: 0 };

        this.onMouseMove = this.onMouseMove.bind(this);
        document.addEventListener('mousemove', this.onMouseMove);
    }

    setSize(width, height) {
        this.width = width;
        this.height = height;
        this.renderer.setSize(width, height);
        this.reset();
        this.center = { x: width / 2, y: height / 2 };
    }

    reset() {
        this.context.font = `${this.fontSize}px ${this.fontFamily}`;
        const charWidth = this.context.measureText('A').width;

        this.cols = Math.floor(this.width / (this.fontSize * (charWidth / this.fontSize)));
        this.rows = Math.floor(this.height / this.fontSize);

        this.canvas.width = this.cols;
        this.canvas.height = this.rows;

        Object.assign(this.pre.style, {
            fontFamily: this.fontFamily,
            fontSize: `${this.fontSize}px`,
            margin: '0', padding: '0', lineHeight: '1em',
            position: 'absolute', left: '0', top: '0', width: '100%', height: '100%',
            overflow: 'hidden', whiteSpace: 'pre'
        });
    }

    render(scene, camera) {
        this.renderer.render(scene, camera);

        const w = this.canvas.width;
        const h = this.canvas.height;
        this.context.clearRect(0, 0, w, h);
        if (w && h) {
            this.context.drawImage(this.renderer.domElement, 0, 0, w, h);
        }

        this.asciify(this.context, w, h);
        // this.hue(); // Optional hue rotation
    }

    onMouseMove(e) {
        this.mouse = { x: e.clientX * PX_RATIO, y: e.clientY * PX_RATIO };
    }

    asciify(ctx, w, h) {
        if (!w || !h) return;
        const imgData = ctx.getImageData(0, 0, w, h).data;
        let str = '';
        const len = this.charset.length;

        for (let y = 0; y < h; y++) {
            for (let x = 0; x < w; x++) {
                const i = (x + y * w) * 4;
                const [r, g, b, a] = [imgData[i], imgData[i + 1], imgData[i + 2], imgData[i + 3]];

                if (a === 0) {
                    str += ' ';
                    continue;
                }

                const gray = (0.3 * r + 0.6 * g + 0.1 * b) / 255;
                let idx = Math.floor((1 - gray) * (len - 1));
                if (this.invert) idx = len - idx - 1;

                // Color support could be added here by wrapping spans
                str += this.charset[idx] || ' ';
            }
            str += '\n';
        }
        this.pre.textContent = str;
    }
}

class CanvasTxt {
    constructor(txt, { fontSize = 200, fontFamily = 'Arial', color = '#fdf9f3' } = {}) {
        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d');
        this.txt = txt;
        this.fontSize = fontSize;
        this.fontFamily = fontFamily;
        this.color = color;
        this.font = `600 ${this.fontSize}px ${this.fontFamily}`;
    }

    resize() {
        this.context.font = this.font;
        const metrics = this.context.measureText(this.txt);
        this.canvas.width = Math.ceil(metrics.width) + 20;
        this.canvas.height = Math.ceil(metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent) + 40;
    }

    render() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.context.fillStyle = this.color;
        this.context.font = this.font;
        this.context.textBaseline = 'middle';
        this.context.fillText(this.txt, 10, this.canvas.height / 2);
    }
}

class CanvAscii {
    constructor(options, container, width, height) {
        this.options = options;
        this.container = container;
        this.width = width;
        this.height = height;

        this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 1, 1000);
        this.camera.position.z = 30;
        this.scene = new THREE.Scene();
    }

    init() {
        this.textCanvas = new CanvasTxt(this.options.text, {
            fontSize: this.options.textFontSize,
            fontFamily: 'Instrument Sans, sans-serif', // Use project font
            color: this.options.textColor
        });
        this.textCanvas.resize();
        this.textCanvas.render();

        this.texture = new THREE.CanvasTexture(this.textCanvas.canvas);
        this.texture.minFilter = THREE.NearestFilter;

        const aspect = this.textCanvas.canvas.width / this.textCanvas.canvas.height;
        const planeH = this.options.planeBaseHeight;
        const planeW = planeH * aspect;

        this.geometry = new THREE.PlaneGeometry(planeW, planeH, 36, 36);
        this.material = new THREE.ShaderMaterial({
            vertexShader,
            fragmentShader,
            transparent: true,
            uniforms: {
                uTime: { value: 0 },
                mouse: { value: 1.0 },
                uTexture: { value: this.texture },
                uEnableWaves: { value: this.options.enableWaves ? 1.0 : 0.0 }
            }
        });

        this.mesh = new THREE.Mesh(this.geometry, this.material);
        this.scene.add(this.mesh);

        this.renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true });
        this.renderer.setSize(this.width, this.height);
        this.renderer.setClearColor(0x000000, 0);

        this.filter = new AsciiFilter(this.renderer, {
            fontFamily: 'monospace',
            fontSize: this.options.asciiFontSize,
            invert: true
        });

        this.container.appendChild(this.filter.domElement);
        this.filter.setSize(this.width, this.height);
        this.animate();
    }

    animate() {
        if (!this.renderer) return;
        requestAnimationFrame(this.animate.bind(this));

        const time = Date.now() * 0.001;
        this.mesh.material.uniforms.uTime.value = Math.sin(time);

        // Slight rotation based on mouse or auto
        this.mesh.rotation.x = Math.sin(time * 0.5) * 0.1;
        this.mesh.rotation.y = Math.cos(time * 0.3) * 0.1;

        this.filter.render(this.scene, this.camera);
    }

    resize(w, h) {
        this.width = w;
        this.height = h;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
        this.filter.setSize(w, h);
    }
}

export function initASCIIText(containerId, {
    text = "Sankalp",
    asciiFontSize = 8,
    textFontSize = 150,
    textColor = '#ffffff',
    planeBaseHeight = 12,
    enableWaves = true
} = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Hide fallback if present
    const fallback = document.getElementById('ascii-fallback');
    if (fallback) fallback.style.display = 'none';

    // Clear previous
    container.innerHTML = '';

    // Add gradient style for the text
    const style = document.createElement('style');
    style.innerHTML = `
        #${containerId} pre {
            background: linear-gradient(to bottom, #7F5AF0, #2CB67D);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            mix-blend-mode: hard-light;
            font-weight: 700;
        }
    `;
    container.appendChild(style);

    const instance = new CanvAscii(
        { text, asciiFontSize, textFontSize, textColor, planeBaseHeight, enableWaves },
        container,
        container.clientWidth,
        container.clientHeight
    );
    instance.init();

    window.addEventListener('resize', () => {
        instance.resize(container.clientWidth, container.clientHeight);
    });

    return instance;
}
