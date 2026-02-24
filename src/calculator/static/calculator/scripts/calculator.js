function toggle(id) {
  document.getElementById(id).classList.toggle('open');
}

const labelMap = {
  eye:        { brown: 'Карі', green: 'Зелені', blue: 'Блакитні', gray: 'Сірі', hazel: 'Горіхові' },
  hair_color: { black: 'Чорне', dark_brown: 'Темно-каштанове', brown: 'Каштанове', blonde: 'Русяве', red: 'Руде' },
  hair_type:  { straight: 'Пряме', wavy: 'Хвилясте', curly: 'Кучеряве' },
  blood:      { O: 'I (O)', A: 'II (A)', B: 'III (B)', AB: 'IV (AB)' },
  rh:         { pos: 'Rh+', neg: 'Rh−' },
  height:     { tall: 'Високий', medium: 'Середній', short: 'Низький' },
  yn:         { yes: 'Є', no: 'Немає' },
};

function badge(badgeId, select, trait, prefix) {
  const el = document.getElementById(badgeId);
  const v = select.value;
  const label = labelMap[trait] && labelMap[trait][v];

  if (label) {
    el.textContent = prefix + label;
    el.classList.add('visible');
  } else {
    el.textContent = '';
    el.classList.remove('visible');
  }
}
