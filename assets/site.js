// Phone menu
const menuButton = document.querySelector('.menu-button');
if (menuButton) {
  menuButton.addEventListener('click', () => {
    const open = document.querySelector('.sidebar').classList.toggle('open');
    menuButton.setAttribute('aria-expanded', String(open));
  });
}

// The address is stored reversed, so it is not in the page as plain text for spam bots
document.querySelectorAll('.js-email').forEach((link) => {
  const [domain, user] = link.dataset.e.split('|').map((part) => [...part].reverse().join(''));
  link.href = `mailto:${user}@${domain}`;
});

// Publication filter: without JavaScript the buttons stay hidden and every entry shows
const filter = document.querySelector('.filter');
if (filter) {
  filter.hidden = false;
  const buttons = filter.querySelectorAll('button');
  const show = (name) => {
    buttons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.filter === name)));
    document.querySelectorAll('.pub-section').forEach((section) => {
      let visible = 0;
      section.querySelectorAll('.pub').forEach((pub) => {
        const match = name === 'all' || pub.dataset[name] === 'true';
        pub.hidden = !match;
        if (match) visible += 1;
      });
      section.hidden = visible === 0;
    });
  };
  buttons.forEach((b) => b.addEventListener('click', () => show(b.dataset.filter)));
}
