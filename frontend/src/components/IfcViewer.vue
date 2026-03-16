<template>
  <div class="ifc-viewer-wrapper">
    <div ref="ifcContainer" class="ifc-container"></div>
    
    <!-- Loading Overlay -->
    <div v-if="loading" class="ifc-loading-overlay">
      <el-icon class="is-loading"><Loading /></el-icon>
      <div class="loading-text">正在生成 3D 地图...</div>
    </div>

    <!-- UI Controls -->
    <div class="ifc-controls" v-if="!loading">
      <el-button-group>
        <el-tooltip content="回到中心视角" placement="bottom">
          <el-button size="small" :icon="ZoomIn" @click="handleZoomFit">聚焦车位</el-button>
        </el-tooltip>
        <el-button size="small" :icon="Refresh" @click="buildNativeScene">刷新模型</el-button>
      </el-button-group>
    </div>

    <!-- Legend -->
    <div class="ifc-legend glass-effect" v-if="!loading">
      <div class="legend-item"><span class="swatch available"></span>空闲</div>
      <div class="legend-item"><span class="swatch occupied"></span>占用</div>
      <div class="legend-item"><span class="swatch reserved"></span>预约</div>
      <div class="legend-item"><span class="swatch maintenance"></span>维护</div>
    </div>

    <div class="ifc-info-badge" v-if="!loading">
      当前区域 • 共 {{ spots.length }} 个泊位
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { ZoomIn, Refresh, Loading } from '@element-plus/icons-vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

// 移除 IFC 加载器，改用原生 Three.js 构建轻量化 3D 场景
const props = defineProps({
  ifcUrl: { type: String, required: true },
  spots: { type: Array, default: () => [] }
});

const ifcContainer = ref(null);
const loading = ref(true);

const emit = defineEmits(['spot-click']);

let scene, camera, renderer, controls;
let spotMeshes = {}; // spot_no -> mesh
let animationId;

// 调色盘
const colors = {
  0: '#4ade80', // Green
  1: '#3b82f6', // Blue
  2: '#94a3b8', // Gray
  3: '#f59e0b'  // Orange
};

const hexToNum = (hex) => parseInt(hex.replace('#', '0x'));

// 基本材质，用于无纹理时备用
const statusMaterials = {
  0: new THREE.MeshStandardMaterial({ color: hexToNum(colors[0]), emissive: 0x166534, emissiveIntensity: 0.2, roughness: 0.2, metalness: 0.1 }),
  1: new THREE.MeshStandardMaterial({ color: hexToNum(colors[1]), emissive: 0x1e3a8a, emissiveIntensity: 0.2, roughness: 0.2, metalness: 0.8 }),
  2: new THREE.MeshStandardMaterial({ color: hexToNum(colors[2]), emissive: 0x475569, emissiveIntensity: 0.1, roughness: 0.8, metalness: 0.0 }),
  3: new THREE.MeshStandardMaterial({ color: hexToNum(colors[3]), emissive: 0x92400e, emissiveIntensity: 0.3, roughness: 0.3, metalness: 0.5 })
};

// 动态创建带有车位编号 Canvas 贴图的材质
const createSpotMaterial = (text, status) => {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  
  // 背景颜色
  ctx.fillStyle = colors[status] || colors[0];
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  // 边框 - 让车位看起来更像格子
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
  ctx.lineWidth = 12;
  ctx.strokeRect(6, 6, canvas.width - 12, canvas.height - 12);

  // 内部虚线
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
  ctx.lineWidth = 4;
  ctx.setLineDash([20, 20]);
  ctx.strokeRect(30, 30, canvas.width - 60, canvas.height - 60);
  ctx.setLineDash([]); // reset

  // 文字：车位编号
  ctx.fillStyle = '#ffffff';
  ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
  ctx.shadowBlur = 8;
  ctx.shadowOffsetY = 2;
  ctx.font = 'bold 70px "Inter", "Helvetica Neue", Arial, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  
  // 旋转并绘制文字，使其在车位上正向纵向显示
  ctx.save();
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate(-Math.PI / 2); 
  ctx.fillText(text, 0, 0);
  ctx.restore();

  const texture = new THREE.CanvasTexture(canvas);
  texture.anisotropy = renderer && renderer.capabilities ? renderer.capabilities.getMaxAnisotropy() : 4;

  const matColor = hexToNum(colors[status] || colors[0]);
  
  return new THREE.MeshStandardMaterial({
    map: texture,
    color: 0xffffff, // 必须为纯白，否则材质底色会与贴图相乘，导致白字被染色而变不可见
    roughness: 0.3,
    metalness: 0.1,
    emissive: matColor,
    emissiveIntensity: 0.15
  });
};

const initScene = () => {
  if (!ifcContainer.value) return;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf1f5f9);

  const width = ifcContainer.value.clientWidth || 800;
  const height = ifcContainer.value.clientHeight || 550;

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  
  setupLightsAndEnvironment();

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  
  ifcContainer.value.innerHTML = '';
  ifcContainer.value.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

  const animate = () => {
    if (!renderer) return;
    animationId = requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  };
  animate();

  renderer.domElement.addEventListener('click', onMouseClick);
  // Pointer cursor when hovering over interactive canvas
  renderer.domElement.style.cursor = 'crosshair';
};

const setupLightsAndEnvironment = () => {
  const ambient = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambient);

  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.position.set(50, 100, 30);
  dirLight.castShadow = true;
  dirLight.shadow.mapSize.width = 2048;
  dirLight.shadow.mapSize.height = 2048;
  dirLight.shadow.camera.near = 0.5;
  dirLight.shadow.camera.far = 500;
  dirLight.shadow.camera.left = -50;
  dirLight.shadow.camera.right = 50;
  dirLight.shadow.camera.top = 50;
  dirLight.shadow.camera.bottom = -50;
  dirLight.shadow.bias = -0.0001;
  scene.add(dirLight);

  const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.4);
  hemiLight.position.set(0, 50, 0);
  scene.add(hemiLight);

  // 增加地面网格
  const groundGeo = new THREE.PlaneGeometry(200, 200);
  const groundMat = new THREE.MeshStandardMaterial({ 
    color: 0xffffff, 
    roughness: 0.9,
    metalness: 0.1 
  });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.05;
  ground.receiveShadow = true;
  scene.add(ground);

  const grid = new THREE.GridHelper(100, 40, 0xcbd5e1, 0xe2e8f0);
  grid.position.y = -0.04;
  scene.add(grid);
};

const clearScene = () => {
  if (!scene) return;
  const toRemove = scene.children.filter(c => c.userData?.isSpot || c.userData?.isDecoration);
  toRemove.forEach(c => {
    scene.remove(c);
    if(c.geometry) c.geometry.dispose();
    if(c.material) {
        if(Array.isArray(c.material)) c.material.forEach(m => m.dispose());
        else c.material.dispose();
    }
  });
  spotMeshes = {};
};

// 核心逻辑：自己生成 3D 地图替代 IFC
const buildNativeScene = () => {
  if (!scene) return;
  loading.value = true;
  clearScene();

  if (!props.spots || props.spots.length === 0) {
    loading.value = false;
    return;
  }

  // 尺寸设定: 车位 宽 2.5m, 长 5m, 厚 0.2m
  const spotWidth = 2.6;
  const spotLength = 5.2;
  const spotThickness = 0.15;
  const spotGeom = new THREE.BoxGeometry(spotWidth, spotThickness, spotLength);
  
  // 用于计算包围盒，以便镜头居中
  const bounds = new THREE.Box3();

  props.spots.forEach((spot, index) => {
    let x = 0, z = 0;
    const i = index + 1;
    const prefix = spot.spot_no.charAt(0).toUpperCase();
    
    // 区划布局算法：根据前缀决定不同的停车场阵型
    if (prefix === 'A') {
      // 对向两排阵型
      const cols = Math.ceil(props.spots.length / 2);
      if (i <= cols) {
        x = (i - 1) * (spotWidth + 0.5);
        z = -(spotLength / 2 + 1);
      } else {
        x = (i - cols - 1) * (spotWidth + 0.5);
        z = (spotLength / 2 + 1);
      }
    } else if (prefix === 'B') {
      // 紧密交错阵型
      const maxCols = 5;
      const row = Math.floor((i - 1) / maxCols);
      const col = (i - 1) % maxCols;
      x = col * (spotWidth + 0.5);
      z = row * (spotLength + 2.0);
    } else {
      // 线性一排阵型 (Visitor)
      x = (i - 1) * (spotWidth + 1.0);
      z = 0;
    }

    // 材质
    const material = createSpotMaterial(spot.spot_no, spot.status);
    
    // 创建 Mesh
    const mesh = new THREE.Mesh(spotGeom, material);
    mesh.position.set(x, spotThickness / 2, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    
    // 增加细微的边缘线，使其具有设计感
    const edges = new THREE.EdgesGeometry(spotGeom);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3 }));
    mesh.add(line);
    
    // 挂载业务数据，用于点击交互
    mesh.userData = { 
      isSpot: true, 
      spot_no: spot.spot_no, 
      status: spot.status 
    };
    
    scene.add(mesh);
    spotMeshes[spot.spot_no] = mesh;
    bounds.expandByObject(mesh);
  });
  
  // 添加一些装饰物 (隔离墩/绿化带) 给场景增加细节
  addDecorations(bounds);

  loading.value = false;
  
  // 根据包围盒自动调整镜头
  setTimeout(() => handleZoomFit(bounds), 100);
};

const addDecorations = (bounds) => {
  if (bounds.isEmpty()) return;
  const center = new THREE.Vector3();
  bounds.getCenter(center);
  const size = new THREE.Vector3();
  bounds.getSize(size);

  // 在两侧加上墙体或路沿
  const curbGeo = new THREE.BoxGeometry(size.x + 10, 0.3, 1);
  const curbMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.8 });
  
  const curb1 = new THREE.Mesh(curbGeo, curbMat);
  curb1.position.set(center.x, 0.15, bounds.max.z + 4);
  curb1.castShadow = true;
  curb1.userData.isDecoration = true;
  scene.add(curb1);

  const curb2 = new THREE.Mesh(curbGeo, curbMat);
  curb2.position.set(center.x, 0.15, bounds.min.z - 4);
  curb2.castShadow = true;
  curb2.userData.isDecoration = true;
  scene.add(curb2);
};

// 状态同步更新
const updateStatusMaterials = () => {
  if (!scene) return;
  props.spots.forEach(spot => {
    const mesh = spotMeshes[spot.spot_no];
    if (mesh && mesh.userData.status !== spot.status) {
      // 释放旧材质的贴图内存防止泄漏
      if (mesh.material.map) mesh.material.map.dispose();
      mesh.material.dispose();
      
      mesh.material = createSpotMaterial(spot.spot_no, spot.status);
      mesh.userData.status = spot.status;
      
      // 更新动画效果: 轻微的弹跳提示
      animateSpotUpdate(mesh);
    }
  });
};

const animateSpotUpdate = (mesh) => {
  const originalY = mesh.position.y;
  let frame = 0;
  const animateHop = () => {
    frame++;
    mesh.position.y = originalY + Math.sin(frame * 0.2) * 1.5 * Math.max(0, 1 - frame/30);
    if (frame < 30) {
      requestAnimationFrame(animateHop);
    } else {
      mesh.position.y = originalY;
    }
  };
  animateHop();
};

const handleZoomFit = (passedBounds = null) => {
  if (!camera || !controls || !scene) return;
  
  let bounds = passedBounds;
  if (!bounds || bounds.isEmpty()) {
     bounds = new THREE.Box3();
     Object.values(spotMeshes).forEach(m => bounds.expandByObject(m));
  }
  
  if (bounds.isEmpty()) return;

  const center = new THREE.Vector3();
  bounds.getCenter(center);
  
  const size = new THREE.Vector3();
  bounds.getSize(size);
  
  const maxDim = Math.max(size.x, size.z);
  const fov = camera.fov * (Math.PI / 180);
  let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
  
  // 倾斜视角 (类似 2.5D 视角)
  camera.position.set(center.x + cameraZ * 0.4, cameraZ * 1.2, center.z + cameraZ * 0.8);
  controls.target.set(center.x, 0, center.z); 
  controls.update();
};

const onMouseClick = (event) => {
  if (!ifcContainer.value || !renderer || !camera || loading.value) return;
  const rect = renderer.domElement.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  
  const raycaster = new THREE.Raycaster();
  raycaster.setFromCamera({ x, y }, camera);
  
  // 只与车位交互
  const interactableObjects = scene.children.filter(c => c.userData.isSpot);
  const intersects = raycaster.intersectObjects(interactableObjects);
  
  if (intersects.length > 0) {
    const obj = intersects[0].object;
    if (obj.userData && obj.userData.spot_no) {
      // 触发交互动画
      const origScale = obj.scale.clone();
      obj.scale.set(0.9, 0.9, 0.9);
      setTimeout(() => obj.scale.copy(origScale), 100);
      
      emit('spot-click', obj.userData.spot_no);
    }
  }
};

const onWindowResize = () => {
  if (!ifcContainer.value || !renderer || !camera) return;
  const width = ifcContainer.value.clientWidth;
  const height = ifcContainer.value.clientHeight;
  if (width === 0 || height === 0) return;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
};

let resizeObserver;

// 当区域文件切换时，重新构建整个 3D 布局
watch(() => props.ifcUrl, () => { 
  if (props.spots && props.spots.length > 0) buildNativeScene(); 
});

// 当状态发生变化时，仅更新对应的材质，不重建场景
watch(() => props.spots, (newSpots, oldSpots) => { 
  if (Object.keys(spotMeshes).length === 0) {
    buildNativeScene();
  } else {
    updateStatusMaterials(); 
  }
}, { deep: true });

onMounted(() => {
  initScene();
  buildNativeScene();
  resizeObserver = new ResizeObserver(() => onWindowResize());
  if (ifcContainer.value) resizeObserver.observe(ifcContainer.value);
});

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId);
  if (resizeObserver) resizeObserver.disconnect();
  if (renderer) {
    renderer.domElement.removeEventListener('click', onMouseClick);
    renderer.dispose();
  }
});
</script>

<style scoped>
.ifc-viewer-wrapper {
  position: relative;
  width: 100%;
  height: 550px;
  background: #f1f5f9;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: inset 0 2px 20px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
}

.ifc-container {
  width: 100%;
  height: 100%;
}

.ifc-loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(241, 245, 249, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 100;
  color: #1e3a8a;
  gap: 12px;
}

.loading-text {
  font-weight: 600;
  font-size: 14px;
}

.ifc-legend {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.5);
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  z-index: 10;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #475569;
  font-weight: 600;
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
}

.swatch.available { background: #4ade80; }
.swatch.occupied { background: #3b82f6; }
.swatch.reserved { background: #f59e0b; }
.swatch.maintenance { background: #94a3b8; }

.ifc-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 20;
}

.ifc-info-badge {
  position: absolute;
  bottom: 20px;
  left: 20px;
  padding: 6px 14px;
  background: rgba(30, 58, 138, 0.05);
  border-radius: 20px;
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  border: 1px solid rgba(0,0,0,0.05);
}

.glass-effect {
  background: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(8px);
}
</style>
