window.addEventListener('load', function() {
    const container = document.querySelector('.photo-box');
    const infoContainer = document.getElementById('dynamic-info');
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

    controls.minDistance = 5;
    controls.maxDistance = 45;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const colors = {
        adenine: 0xFF6B6B,
        thymine: 0x6BCB77,
        cytosine: 0xFFD93D,
        guanine: 0x4D96FF,
        backbone: 0xFFFFFF,
        highlight: 0xFFFFFF 
    };

    const infoTexts = {
        'A': `<h2>Аденін (A)</h2><p>Аденін — одна з чотирьох основ ДНК. Він завжди поєднується з тиміном (T), утворюючи пару, яка підтримує стабільну структуру подвійної спіралі.</p>`,
        'T': `<h2>Тимін (T)</h2><p>Тимін завжди зв’язується з аденіном (A). Ця пара забезпечує стабільність подвійної спіралі та правильне копіювання ДНК під час поділу клітин.</p>`,
        'G': `<h2>Гуанін (G)</h2><p>Гуанін утворює пару з цитозином (C). Ці зв’язки допомагають утримувати подвійний ланцюг ДНК міцним, але дозволяють йому розкручуватися для роботи клітини.</p>`,
        'C': `<h2>Цитозин (C)</h2><p>Цитозин завжди поєднується з гуаніном (G). Пара C–G підтримує стабільну структуру ДНК і забезпечує точне зчитування генетичної інформації.</p>`,
        'default': `<h2>Що таке ДНК?</h2>
                    <p>ДНК — це молекула, яка зберігає всю генетичну інформацію організму. Вона складається з чотирьох основних нуклеотидів — аденіну, тиміну, гуаніну та цитозину, які завжди формують стабільні пари: A з T та G з C. Саме ця структура утворює відому подвійною спіраль і забезпечує точне копіювання генетичної інформації під час росту та поділу клітин.</p>
                    <p>На нашому сайті ви можете не лише побачити, як виглядає ДНК, а й дізнатися цікаві факти про нуклеотиди, їхні функції та роль у житті організму. Інтерактивна модель дозволяє натискати на елементи та отримувати короткі пояснення, що допомагає зрозуміти складну біологію просто та наочно.</p>`
    };

    const tubeGeo = new THREE.CylinderGeometry(0.45, 0.45, 6, 32);
    const ballGeo = new THREE.SphereGeometry(1.1, 32, 32);
    const dnaGroup = new THREE.Group();

    for (let i = 0; i <= 40; i++) {
        const row = new THREE.Group();
        let lCol, rCol, lType, rType;

        if (Math.random() > 0.5) { 
            [lCol, rCol] = [colors.adenine, colors.thymine]; 
            [lType, rType] = ['A', 'T'];
        } else { 
            [lCol, rCol] = [colors.cytosine, colors.guanine]; 
            [lType, rType] = ['C', 'G'];
        }

        const leftTube = new THREE.Mesh(tubeGeo, new THREE.MeshBasicMaterial({ color: lCol }));
        leftTube.rotation.z = Math.PI / 2;
        leftTube.position.x = -3;
        leftTube.userData = { originalColor: lCol, baseType: lType };

        const rightTube = new THREE.Mesh(tubeGeo, new THREE.MeshBasicMaterial({ color: rCol }));
        rightTube.rotation.z = Math.PI / 2;
        rightTube.position.x = 3;
        rightTube.userData = { originalColor: rCol, baseType: rType };

        const ballL = new THREE.Mesh(ballGeo, new THREE.MeshBasicMaterial({ color: colors.backbone }));
        ballL.position.x = -6;
        ballL.userData = { originalColor: colors.backbone, baseType: 'default' };

        const ballR = new THREE.Mesh(ballGeo, new THREE.MeshBasicMaterial({ color: colors.backbone }));
        ballR.position.x = 6;
        ballR.userData = { originalColor: colors.backbone, baseType: 'default' };

        row.add(leftTube, rightTube, ballL, ballR);
        row.position.y = (i - 20) * 2.2; 
        row.rotation.y = (i * 30) * Math.PI / 180;
        dnaGroup.add(row);
    }
    scene.add(dnaGroup);

    function onClick(event) {
        const rect = container.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(dnaGroup.children, true);

        dnaGroup.traverse((child) => {
            if (child.isMesh) {
                child.material.color.setHex(child.userData.originalColor);
            }
        });

        let type = 'default';

        if (intersects.length > 0) {
            const clickedPart = intersects[0].object;
            type = clickedPart.userData.baseType;

            clickedPart.material.color.setHex(colors.highlight);
        }

        if (infoContainer && infoTexts[type]) {
            infoContainer.style.opacity = 0; 
            
            setTimeout(() => {
                infoContainer.innerHTML = infoTexts[type];
                infoContainer.style.opacity = 1; 
            }, 200);
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
        const newWidth = container.clientWidth;
        const newHeight = container.clientHeight;
        renderer.setSize(newWidth, newHeight);
        camera.aspect = newWidth / newHeight;
        camera.updateProjectionMatrix();
    });
});
