/* Lightweight, reusable form step tabs.
 *
 * Markup convention:
 *   <form novalidate>
 *     <div data-form-tabs>
 *       <div class="dh-form-tab-nav">
 *         <button type="button" data-form-tab data-tab-target="pane-id">...</button>
 *       </div>
 *       <div class="dh-form-tab-pane" id="pane-id" data-form-tab-pane>...</div>
 *     </div>
 *   </form>
 *
 * The helper keeps hidden tabs out of native validation (forms use novalidate)
 * so a required field in a later tab can still be validated and focused.
 */
(function () {
  'use strict';

  function rootOf(element) {
    return element ? element.closest('[data-form-tabs]') : null;
  }

  function tabButtons(root) {
    return root ? Array.prototype.slice.call(root.querySelectorAll('[data-form-tab]')) : [];
  }

  function panesOf(root) {
    return root ? Array.prototype.slice.call(root.querySelectorAll('[data-form-tab-pane]')) : [];
  }

  function paneForTarget(root, targetId) {
    if (!root || !targetId) return null;
    var pane = document.getElementById(targetId);
    return pane && root.contains(pane) ? pane : null;
  }

  function activate(root, pane) {
    if (!root || !pane) return;

    panesOf(root).forEach(function (candidate) {
      var isActive = candidate === pane;
      candidate.classList.toggle('is-active', isActive);
      if (isActive) {
        candidate.removeAttribute('hidden');
        candidate.setAttribute('aria-hidden', 'false');
      } else {
        candidate.setAttribute('hidden', '');
        candidate.setAttribute('aria-hidden', 'true');
      }
    });

    tabButtons(root).forEach(function (button) {
      var isActive = button.getAttribute('data-tab-target') === pane.id;
      button.classList.toggle('is-active', isActive);
      button.setAttribute('aria-selected', isActive ? 'true' : 'false');
      button.tabIndex = isActive ? 0 : -1;
    });
  }

  function formFields(scope) {
    return Array.prototype.slice
      .call(scope.querySelectorAll('input, select, textarea'))
      .filter(function (field) {
        return !field.disabled && field.type !== 'hidden' && field.type !== 'button';
      });
  }

  function firstInvalid(scope) {
    return formFields(scope).find(function (field) {
      return !field.checkValidity();
    }) || null;
  }

  function focusInvalid(field) {
    window.setTimeout(function () {
      try {
        field.focus({ preventScroll: false });
      } catch (error) {
        field.focus();
      }
      if (typeof field.reportValidity === 'function') {
        field.reportValidity();
      }
    }, 30);
  }

  function validatePane(pane) {
    var invalid = firstInvalid(pane);
    if (!invalid) return true;
    focusInvalid(invalid);
    return false;
  }

  function validate(form) {
    if (!form) return true;

    var root = form.querySelector('[data-form-tabs]');
    if (!root) {
      var invalid = firstInvalid(form);
      if (!invalid) return true;
      focusInvalid(invalid);
      return false;
    }

    var panes = panesOf(root);
    for (var index = 0; index < panes.length; index += 1) {
      var currentInvalid = firstInvalid(panes[index]);
      if (currentInvalid) {
        activate(root, panes[index]);
        focusInvalid(currentInvalid);
        return false;
      }
    }

    return true;
  }

  function reset(form) {
    if (!form) return;
    var root = form.querySelector('[data-form-tabs]');
    if (!root) return;
    var panes = panesOf(root);
    if (panes.length) activate(root, panes[0]);
  }

  function showPane(root, pane) {
    activate(root, pane);
  }

  function move(root, pane, step) {
    var panes = panesOf(root);
    var index = panes.indexOf(pane);
    if (index === -1) return;
    var target = panes[index + step];
    if (target) activate(root, target);
  }

  document.addEventListener('click', function (event) {
    var tab = event.target.closest('[data-form-tab]');
    if (tab) {
      var tabRoot = rootOf(tab);
      var targetPane = paneForTarget(tabRoot, tab.getAttribute('data-tab-target'));
      if (tabRoot && targetPane) {
        event.preventDefault();
        activate(tabRoot, targetPane);
      }
      return;
    }

    var next = event.target.closest('[data-tab-next]');
    if (next) {
      var nextRoot = rootOf(next);
      var currentPane = next.closest('[data-form-tab-pane]');
      if (!nextRoot || !currentPane) return;
      event.preventDefault();
      if (!validatePane(currentPane)) return;
      move(nextRoot, currentPane, 1);
      return;
    }

    var previous = event.target.closest('[data-tab-prev]');
    if (previous) {
      var previousRoot = rootOf(previous);
      var previousPane = previous.closest('[data-form-tab-pane]');
      if (!previousRoot || !previousPane) return;
      event.preventDefault();
      move(previousRoot, previousPane, -1);
    }
  });

  document.addEventListener('keydown', function (event) {
    var tab = event.target.closest('[data-form-tab]');
    if (!tab || (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft')) return;
    var root = rootOf(tab);
    var buttons = tabButtons(root);
    var index = buttons.indexOf(tab);
    if (index === -1) return;
    event.preventDefault();
    var nextIndex = event.key === 'ArrowRight'
      ? (index + 1) % buttons.length
      : (index - 1 + buttons.length) % buttons.length;
    var nextButton = buttons[nextIndex];
    var pane = paneForTarget(root, nextButton.getAttribute('data-tab-target'));
    activate(root, pane);
    nextButton.focus();
  });

  window.DHFormTabs = {
    activate: function (form, paneId) {
      if (!form) return;
      var root = form.querySelector('[data-form-tabs]');
      var pane = paneForTarget(root, paneId);
      if (root && pane) activate(root, pane);
    },
    reset: reset,
    validate: validate,
    show: showPane,
  };
})();
