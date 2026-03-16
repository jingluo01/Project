
<template>
  <div class="ifc-viewer-wrapper">
    <div ref="ifcContainer" class="ifc-container" v-loading="loading"></div>
    <div class="ifc-controls">
      <el-button-group>
        <el-button size="small" :icon="ZoomIn" @click="handleZoomFit">全屏缩放</el-button>
        <el-button size="small" :icon="Refresh" @click="handleReload">重新加载</el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { ZoomIn, Refresh } from '@element-plus/icons-vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { IFCLoader } from 'web-ifc-three/IFCLoader';

const props = defineProps({
  ifcUrl: {
    type: String,
    required: true
  }
});

const ifcContainer = ref(null);
const loading = ref(true);

const emit = defineEmits(['spot-click']);

let scene, camera, renderer, controls, loader;

const initScene = () => {
  // Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf1f5f9);

  // Camera
  const width = ifcContainer.value.clientWidth;
  const height = ifcContainer.value.clientHeight;
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(45, 45, 45);

  // Initial Lights
  initSceneLightsAndGrid();

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(window.devicePixelRatio);
  ifcContainer.value.appendChild(renderer.domElement);

  // Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  // Animation Loop
  const animate = () => {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  };
  animate();

  // Click Interaction
  renderer.domElement.addEventListener('click', onMouseClick);
  renderer.domElement.style.cursor = 'pointer';

  // Resize Listener
  window.addEventListener('resize', onWindowResize);
};

const onMouseClick = async (event) => {
  if (!ifcContainer.value || !loader) return;

  const rect = renderer.domElement.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  const raycaster = new THREE.Raycaster();
  raycaster.setFromCamera({ x, y }, camera);

  const intersects = raycaster.intersectObjects(scene.children, true);

  if (intersects.length > 0) {
    const obj = intersects[0].object;
    const index = intersects[0].faceIndex;
    const geometry = obj.geometry;
    const id = loader.ifcManager.getExpressId(geometry, index);
    
    if (id !== undefined) {
      try {
        const props = await loader.ifcManager.getItemProperties(0, id);
        const name = props.Name?.value; // e.g., "A-001"
        if (name && (name.includes('-') || name.startsWith('Spot'))) {
           emit('spot-click', name);
        }
      } catch (err) {
        console.warn('Could not fetch IFC properties for ID:', id);
      }
    }
  }
};

const onWindowResize = () => {
  if (!ifcContainer.value || !renderer) return;
  const width = ifcContainer.value.clientWidth;
  const height = ifcContainer.value.clientHeight;
  if (width === 0 || height === 0) return;
  
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
};

let resizeObserver;

const loadIFC = async () => {
  loading.value = true;
  loader = new IFCLoader();
  loader.ifcManager.setWasmPath('/wasm/');

  loader.load(props.ifcUrl, (ifcModel) => {
    scene.add(ifcModel);
    loading.value = false;
    handleZoomFit();
  }, undefined, (err) => {
    console.error('Error loading IFC:', err);
    loading.value = false;
  });
};

const handleZoomFit = () => {
  if (!camera || !controls) return;
  camera.position.set(45, 45, 45);
  controls.target.set(21, 0, 12); 
  controls.update();
};

const handleReload = () => {
  if (!scene) return;
  scene.children = scene.children.filter(c => !(c.type === 'Group' || c.isLineSegments || c.type === 'Mesh'));
  initSceneLightsAndGrid();
  loadIFC();
};

const initSceneLightsAndGrid = () => {
    const light1 = new THREE.DirectionalLight(0xffffff, 1);
    light1.position.set(1, 1, 1).normalize();
    scene.add(light1);
    const light2 = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(light2);
    const grid = new THREE.GridHelper(50, 50, 0xcccccc, 0xdddddd);
    scene.add(grid);
    const axes = new THREE.AxesHelper(1);
    scene.add(axes);
}

onMounted(() => {
  initScene();
  loadIFC();
  
  resizeObserver = new ResizeObserver(() => {
    onWindowResize();
  });
  if (ifcContainer.value) {
    resizeObserver.observe(ifcContainer.value);
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', onWindowResize);
  if (renderer && renderer.domElement) {
    renderer.domElement.removeEventListener('click', onMouseClick);
  }
  if (resizeObserver) resizeObserver.disconnect();
  if (renderer) renderer.dispose();
});
</script>

<style scoped>
.ifc-viewer-wrapper {
  position: relative;
  width: 100%;
  height: 550px;
  background: #f1f5f9;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.ifc-container {
  width: 100%;
  height: 100%;
}

.ifc-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}
</style>
