const addToggle = document.getElementById('add-restaurant-toggle');
const addPanel = document.getElementById('add-restaurant-panel');
const cancelAdd = document.getElementById('cancel-add-restaurant');
const addIcon = addToggle.querySelector('.add-toggle-icon');

function setAddFormOpen(open) {
  addPanel.hidden = !open;
  addToggle.setAttribute('aria-expanded', String(open));
  addToggle.setAttribute('aria-label', open ? 'Close add restaurant form' : 'Add a restaurant');
  addToggle.title = open ? 'Close add restaurant form' : 'Add a restaurant';
  addIcon.textContent = open ? '×' : '+';
  (open ? document.getElementById('title') : addToggle).focus();
}

addToggle.addEventListener('click', () => setAddFormOpen(addPanel.hidden));
cancelAdd.addEventListener('click', () => setAddFormOpen(false));
addPanel.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') setAddFormOpen(false);
});

const addFormError = document.getElementById('add-form-error');
if (addFormError) addFormError.focus();
else if (!addPanel.hidden) document.getElementById('title').focus();
