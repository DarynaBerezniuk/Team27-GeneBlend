window.addEventListener('load', function() {
    const container = document.querySelector('.photo-box');
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 18; 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.minPolarAngle = Math.PI / 2;
    controls.maxPolarAngle = Math.PI / 2;

    // --- INTERACTION SETUP ---
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const colors = {
        adenine: 0xFF6B6B, thymine: 0x4D96FF,
        cytosine: 0x6BCB77, guanine: 0xFFD93D,
        backbone: 0xFFFFFF,
        highlight: 0xFFFFFF // Color when "lit up"
    };

    const tubeGeo = new THREE.CylinderGeometry(0.45, 0.45, 6, 32);
    const ballGeo = new THREE.SphereGeometry(1.1, 32, 32);
    const dnaGroup = new THREE.Group();

    for (let i = 0; i <= 40; i++) {
        const row = new THREE.Group();
        let lCol, rCol;

        if (Math.random() > 0.5) { [lCol, rCol] = [colors.adenine, colors.thymine]; } 
        else { [lCol, rCol] = [colors.cytosine, colors.guanine]; }

        // We use unique materials for each mesh so we can change them individually
        const leftTube = new THREE.Mesh(tubeGeo, new THREE.MeshBasicMaterial({ color: lCol }));
        leftTube.rotation.z = Math.PI / 2;
        leftTube.position.x = -3;
        // Store original color for resetting later
        leftTube.userData.originalColor = lCol;

        const rightTube = new THREE.Mesh(tubeGeo, new THREE.MeshBasicMaterial({ color: rCol }));
        rightTube.rotation.z = Math.PI / 2;
        rightTube.position.x = 3;
        rightTube.userData.originalColor = rCol;

        const ballL = new THREE.Mesh(ballGeo, new THREE.MeshBasicMaterial({ color: colors.backbone }));
        ballL.position.x = -6;
        ballL.userData.originalColor = colors.backbone;

        const ballR = new THREE.Mesh(ballGeo, new THREE.MeshBasicMaterial({ color: colors.backbone }));
        ballR.position.x = 6;
        ballR.userData.originalColor = colors.backbone;

        row.add(leftTube, rightTube, ballL, ballR);
        row.position.y = (i - 20) * 2.2; 
        row.rotation.y = (i * 30) * Math.PI / 180;
        dnaGroup.add(row);
    }
    scene.add(dnaGroup);

    // --- CLICK FUNCTION ---
    function onClick(event) {
        // Calculate mouse position relative to the photo-box div
        const rect = container.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);

        // Check for hits (true means check children of groups)
        const intersects = raycaster.intersectObjects(dnaGroup.children, true);

        // Reset all parts to original colors first
        dnaGroup.traverse((child) => {
            if (child.isMesh) {
                child.material.color.setHex(child.userData.originalColor);
            }
        });

        // If we hit something, "light it up"
        if (intersects.length > 0) {
            const clickedPart = intersects[0].object;
            clickedPart.material.color.setHex(colors.highlight);
        }
    }

    renderer.domElement.addEventListener('click', onClick);

    function animate() {
        requestAnimationFrame(animate);
        controls.update(); 
        renderer.render(scene, camera);
    }

    animate();

    window.addEventListener('resize', () => {
        renderer.setSize(container.clientWidth, container.clientHeight);
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
    });
});
