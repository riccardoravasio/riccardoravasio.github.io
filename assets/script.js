(function () {
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var explicit = document.documentElement.getAttribute('data-theme');
    var current = explicit || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
})();

(function () {
  var container = document.querySelector('[data-filter-root]');
  if (!container) return;
  var btns = container.querySelectorAll('.filter-btn');
  var entries = container.querySelectorAll('.entry');
  btns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var filter = btn.getAttribute('data-filter');
      btns.forEach(function (b) { b.classList.toggle('active', b === btn); });
      entries.forEach(function (entry) {
        if (filter === 'all') {
          entry.classList.remove('hidden');
          return;
        }
        var tags = (entry.getAttribute('data-tags') || '').split(/\s+/);
        entry.classList.toggle('hidden', tags.indexOf(filter) === -1);
      });
    });
  });
})();
