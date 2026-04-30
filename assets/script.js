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
