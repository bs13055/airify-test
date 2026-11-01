const TEAM = [
  { initials: 'TS', name: 'Thaksin Saardaiam', role: 'Lead Backend Developer', detail: 'Backend Development & API Architecture', photo: 'assets/team/73170.jpg', profile: 'https://jamethaksin.github.io/resume' },
  { initials: 'LR', name: 'Luksanut Rueangkhajon', role: 'Data & AI Engineer', detail: 'Data Analytics & Prediction Models', photo: 'assets/team/73173.jpg', profile: 'https://luksanut.github.io/Reusme/' },
  { initials: 'TC', name: 'Tanawat Chantarawong', role: 'Frontend Developer & UI/UX Designer', detail: 'Web Development & Responsive Design', photo: 'assets/team/73172.jpg', profile: 'https://zentialab.github.io/resume/' },
  { initials: 'NP', name: 'Naphat Phanthong', role: 'Project Lead & Full Stack Developer', detail: 'Product Management & System Integration', photo: 'assets/team/73171.jpg', profile: 'https://bs13055.github.io/resume/' },
];

const root = document.getElementById('teamGrid');
if (root) {
  root.replaceChildren();
  for (const [index, member] of TEAM.entries()) {
    const col = document.createElement('div');
    col.className = 'team-column';

    const card = document.createElement('article');
    card.className = 'member-card h-100';

    const order = document.createElement('span');
    order.className = 'member-index';
    order.textContent = String(index + 1).padStart(2, '0');

    const avatar = document.createElement('div');
    avatar.className = 'avatar member-photo';
    const image = document.createElement('img');
    image.src = member.photo;
    image.alt = member.name;
    image.loading = 'lazy';
    image.decoding = 'async';
    avatar.append(image);

    const name = document.createElement('h3');
    name.textContent = member.name;
    const role = document.createElement('p');
    role.textContent = member.role;
    const detail = document.createElement('small');
    detail.textContent = member.detail;

    card.append(order, avatar, name, role, detail);
    if (member.profile) {
      const link = document.createElement('a');
      link.className = 'member-profile-link';
      link.href = member.profile;
      link.textContent = 'ดู Resume ↗';
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      card.append(link);
    } else {
      const note = document.createElement('small');
      note.className = 'member-profile-pending';
      note.textContent = 'ยังไม่ได้ระบุลิงก์โปรไฟล์';
      card.append(note);
    }

    col.append(card);
    root.append(col);
  }
}
