import * as THREE from './three.module.js';

/**
 * Optimized ASCII Text Effect for Sankalp-AI
 * Renders WebGL at low resolution (one pixel per ASCII char) to maximize performance.
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

    // Gentle wave effect
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
    
    // RGB split / Chromatic aberration for retro feel
    float r = texture2D(uTexture, pos + cos(time * 2. - time + pos.x) * .01).r;
    float g = texture2D(uTexture, pos + tan(time * .5 + pos.x - time) * .01).g;
    float b = texture2D(uTexture, pos - cos(time * 2. + time + pos.y) * .01).b;
    float a = texture2D(uTexture, pos).a;
    
    gl_FragColor = vec4(r, g, b, a);
}
`;

class AsciiFilter {
    constructor(renderer, { fontSize, fontFamily, charset, invert } = {}) {
        this.renderer = renderer;
        this.domElement = document.createElement('div');
        Object.assign(this.domElement.style, {
            position: 'absolute', top: '0', left: '0', 
            width: '100%', height: '100%', 
            pointerEvents: 'none', overflow: 'hidden'
        });

        this.pre = document.createElement('pre');
        this.domElement.appendChild(this.pre);

        // Offscreen canvas for reading pixels
        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d', { willReadFrequently: true });

        this.invert = invert ?? true;
        this.fontSize = fontSize ?? 12;
        this.fontFamily = fontFamily ?? "'Courier New', monospace";
        this.charset = charset ?? ' .\'`^",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$';
        
        // Performance: Limit update rate
        this.lastFrameTime = 0;
        this.fpsFunc = 30; // Target FPS for DOM updates
        this.frameInterval = 1000 / this.fpsFunc;
    }

    setSize(width, height) {
        this.width = width;
        this.height = height;
        
        // Calculate grid dimensions
        // Rough estimate of character aspect ratio (usually ~0.6 for monospace)
        const charAspectRatio = 0.6; 
        this.cols = Math.floor(width / (this.fontSize * charAspectRatio));
        this.rows = Math.floor(height / this.fontSize);

        // CRITICAL OPTIMIZATION:
        // Render Three.js at the resolution of the ASCII grid, NOT the screen.
        // This reduces pixel count by ~200x (if fontSize is 12x20)
        this.renderer.setSize(this.cols, this.rows);
        
        // Resize reading canvas
        this.canvas.width = this.cols;
        this.canvas.height = this.rows;

        // Configure pre tag
        Object.assign(this.pre.style, {
            fontFamily: this.fontFamily,
            fontSize: `${this.fontSize}px`,
            lineHeight: `${this.fontSize}px`,
            margin: '0', padding: '0',
            position: 'absolute', left: '0', top: '0', width: '100%', height: '100%',
            whiteSpace: 'pre',
            transformOrigin: '0 0',
            // Scale width slightly if needed to match aspect ratio
            transform: `scaleX(${charAspectRatio * 1.0})` 
        });
    }

    render(scene, camera) {
        // Render 3D scene to low-res WebGL canvas
        this.renderer.render(scene, camera);

        // Throttle DOM updates
        const now = Date.now();
        if (now - this.lastFrameTime < this.frameInterval) return;
        this.lastFrameTime = now;

        // Read pixels
        const w = this.cols;
        const h = this.rows;
        
        // Draw WebGL output to 2D canvas to get data
        // (Note: readPixels directly from WebGL is faster but context switching is annoying, 
        // drawImage is fast enough for 50x20px images)
        this.context.clearRect(0, 0, w, h);
        if (w && h) {
            this.context.drawImage(this.renderer.domElement, 0, 0, w, h);
            this.asciify(this.context, w, h);
        }
    }

    asciify(ctx, w, h) {
        const imgData = ctx.getImageData(0, 0, w, h).data;
        let str = '';
        const charsetLen = this.charset.length;
        const chars = this.charset;
        const inv = this.invert;

        // Optimization: Use single loop
        for (let i = 0; i < w * h; i++) {
            const idx = i * 4;
            const r = imgData[idx];
            const g = imgData[idx+1];
            const b = imgData[idx+2];
            const a = imgData[idx+3];

            if (a === 0) {
                str += ' ';
            } else {
                const brightness = (0.299*r + 0.587*g + 0.114*b) / 255;
                let charIdx = Math.floor((1 - brightness) * (charsetLen - 1));
                if (inv) charIdx = charsetLen - charIdx - 1;
                
                // Clamp
                if(charIdx < 0) charIdx = 0;
                if(charIdx >= charsetLen) charIdx = charsetLen -1;
                
                str += chars[charIdx];
            }
            
            // Newline at end of row
            if ((i + 1) % w === 0) {
                str += '\n';
            }
        }
        
        // One big DOM update
        this.pre.textContent = str;
    }
}

class CanvasTxt {
    constructor(txt, { fontSize = 150, fontFamily = 'sans-serif', color = '#ffffff' } = {}) {
        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d');
        this.txt = txt;
        this.fontSize = fontSize;
        this.fontFamily = fontFamily;
        this.color = color;
        this.font = `900 ${this.fontSize}px ${this.fontFamily}`;
    }

    resize() {
        this.context.font = this.font;
        const metrics = this.context.measureText(this.txt);
        // Add padding
        this.canvas.width = Math.ceil(metrics.width) + 40;
        this.canvas.height = Math.ceil(this.fontSize * 1.5); // Rough height
        
        this.update();
    }
    
    update() {
        const w = this.canvas.width;
        const h = this.canvas.height;
        this.context.clearRect(0,0,w,h);
        this.context.fillStyle = this.color;
        this.context.font = this.font;
        this.context.textAlign = 'center';
        this.context.textBaseline = 'middle';
        this.context.fillText(this.txt, w/2, h/2);
    }
}

class CanvAscii {
    constructor(options, container) {
        this.options = options;
        this.container = container;
        this.width = container.clientWidth;
        this.height = container.clientHeight;
        
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 1, 1000);
        this.camera.position.z = 30; // Initial zoom
    }

    init() {
        // 1. Prepare Text Texture
        this.textCanvas = new CanvasTxt(this.options.text, {
            fontSize: this.options.textFontSize,
            fontFamily: 'Inter, sans-serif',
            color: this.options.textColor
        });
        this.textCanvas.resize();

        this.texture = new THREE.CanvasTexture(this.textCanvas.canvas);
        this.texture.minFilter = THREE.LinearFilter;
        this.texture.needsUpdate = true;

        // 2. Create Plane
        const aspect = this.textCanvas.canvas.width / this.textCanvas.canvas.height;
        const planeH = this.options.planeBaseHeight; 
        const planeW = planeH * aspect;

        this.geometry = new THREE.PlaneGeometry(planeW, planeH, 32, 16);
        this.material = new THREE.ShaderMaterial({
            vertexShader,
            fragmentShader,
            transparent: true,
            uniforms: {
                uTime: { value: 0 },
                uTexture: { value: this.texture },
                uEnableWaves: { value: this.options.enableWaves ? 1.0 : 0.0 }
            }
        });

        this.mesh = new THREE.Mesh(this.geometry, this.material);
        this.scene.add(this.mesh);

        // 3. Renderer (Low Res)
        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false });
        this.renderer.setClearColor(0x000000, 0);

        // 4. ASCII Filter
        this.filter = new AsciiFilter(this.renderer, {
            fontSize: this.options.asciiFontSize,
            invert: true
        });

        this.container.appendChild(this.filter.domElement);
        this.resize(this.container.clientWidth, this.container.clientHeight);
        
        this.animate();
    }

    animate() {
        if (!this.renderer) return;
        requestAnimationFrame(this.animate.bind(this));

        const time = Date.now() * 0.001;
        this.mesh.material.uniforms.uTime.value = Math.sin(time);
        
        // Subtle floating movement
        this.mesh.rotation.y = Math.sin(time * 0.5) * 0.05;
        this.mesh.position.y = Math.cos(time * 0.8) * 0.2;

        this.filter.render(this.scene, this.camera);
    }

    resize(w, h) {
        this.width = w;
        this.height = h;
        // Keep camera aspect ratio correct for the VIEWPORT
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        
        // Resize filter (which handles internal renderer size)
        this.filter.setSize(w, h);
    }
}

export function initASCIIText(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Remove fallback
    const fallback = document.getElementById('ascii-fallback');
    if (fallback) fallback.style.display = 'none';
    
    // Clear
    const existing = container.querySelector('div');
    if(existing) existing.remove();
    const existingStyle = container.querySelector('style');
    if(existingStyle) existingStyle.remove();

    // Add necessary styling
    const style = document.createElement('style');
    style.innerHTML = `
        #${containerId} pre {
            background: linear-gradient(135deg, #7F5AF0 0%, #2CB67D 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            font-weight: 700;
            line-height: ${options.asciiFontSize || 8}px;
            user-select: none;
        }
    `;
    container.appendChild(style);

    const instance = new CanvAscii(options, container);
    instance.init();

    window.addEventListener('resize', () => {
        instance.resize(container.clientWidth, container.clientHeight);
    });

    return instance;
}
