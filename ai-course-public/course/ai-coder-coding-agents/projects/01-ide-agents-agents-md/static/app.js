/**
 * Kanban board front-end.
 *
 * Vanilla ES modules — no framework, no build step. This is deliberate: the
 * course spends a lecture on why "add a bundler" is almost always the wrong
 * reflex at this size.
 *
 * Drag-and-drop here uses the native HTML5 DnD API. It is verbose and it has
 * sharp edges (those edges are the lecture content), but it has no dependency.
 */

const COLUMNS = [
  { id: "backlog", label: "Backlog" },
  { id: "in_progress", label: "In Progress" },
  { id: "done", label: "Done" },
];

const boardEl = document.getElementById("board");
const formEl = document.getElementById("new-card-form");
const titleInput = document.getElementById("new-card-title");
const cardTemplate = document.getElementById("card-template");

/** Card currently being dragged, held across dragstart -> drop. */
let draggedCard = null;

/* ------------------------------------------------------------------ */
/* API                                                                 */
/* ------------------------------------------------------------------ */

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${options.method ?? "GET"} ${path} -> ${res.status}: ${detail}`);
  }
  return res.status === 204 ? null : res.json();
}

/* ------------------------------------------------------------------ */
/* Render                                                              */
/* ------------------------------------------------------------------ */

function renderColumn({ id, label }) {
  const col = document.createElement("section");
  col.className = "column";
  col.dataset.column = id;

  const header = document.createElement("div");
  header.className = "column-header";

  const title = document.createElement("span");
  title.textContent = label;

  const count = document.createElement("span");
  count.className = "column-count";
  count.dataset.role = "count";

  header.append(title, count);
  col.append(header);
  return col;
}

function renderCard(card) {
  const node = cardTemplate.content.firstElementChild.cloneNode(true);
  node.dataset.id = String(card.id);
  node.querySelector(".card-title").textContent = card.title;

  const desc = node.querySelector(".card-description");
  desc.textContent = card.description ?? "";

  node.querySelector(".card-delete").addEventListener("click", async () => {
    try {
      await api(`/api/cards/${card.id}`, { method: "DELETE" });
      node.remove();
      updateCounts();
    } catch (err) {
      console.error(err);
      alert(`Could not delete card: ${err.message}`);
    }
  });

  attachDragHandlers(node, card);
  return node;
}

function updateCounts() {
  for (const { id } of COLUMNS) {
    const col = boardEl.querySelector(`.column[data-column="${id}"]`);
    if (!col) continue;
    const count = col.querySelector('[data-role="count"]');
    // Exclude the drop placeholder if one is present.
    count.textContent = String(
      col.querySelectorAll(".card:not(.dragging)").length,
    );
  }
}

async function loadBoard() {
  const cards = await api("/api/cards");
  boardEl.replaceChildren();

  const colMap = new Map();
  for (const meta of COLUMNS) {
    const el = renderColumn(meta);
    colMap.set(meta.id, el);
    boardEl.append(el);
  }

  for (const card of cards) {
    const col = colMap.get(card.column) ?? colMap.get("backlog");
    col.append(renderCard(card));
  }
  updateCounts();
}

/* ------------------------------------------------------------------ */
/* Drag and drop                                                       */
/* ------------------------------------------------------------------ */

function attachDragHandlers(node, card) {
  node.addEventListener("dragstart", (event) => {
    draggedCard = { card, node };
    node.classList.add("dragging");
    event.dataTransfer.effectAllowed = "move";
    // Firefox refuses to start a drag unless some data is set.
    event.dataTransfer.setData("text/plain", String(card.id));
  });

  node.addEventListener("dragend", () => {
    node.classList.remove("dragging");
    draggedCard = null;
    boardEl
      .querySelectorAll(".column")
      .forEach((c) => c.classList.remove("drag-over"));
    updateCounts();
  });
}

function wireColumnDropTargets() {
  for (const col of boardEl.querySelectorAll(".column")) {
    const columnId = col.dataset.column;

    // dragover fires continuously; preventDefault is what permits a drop.
    col.addEventListener("dragover", (event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      col.classList.add("drag-over");
    });

    col.addEventListener("dragleave", (event) => {
      // Ignore dragleave events fired by moving onto a child element.
      if (col.contains(event.relatedTarget)) return;
      col.classList.remove("drag-over");
    });

    col.addEventListener("drop", async (event) => {
      event.preventDefault();
      col.classList.remove("drag-over");
      if (!draggedCard) return;

      const { card, node } = draggedCard;
      const siblings = [...col.querySelectorAll(".card:not(.dragging)")];
      // Drop position = index of the card we were dropped above, else append.
      const after = siblings.find((s) =>
        event.clientY < s.getBoundingClientRect().top + s.offsetHeight / 2,
      );
      const position = after ? siblings.indexOf(after) : siblings.length;

      // Optimistic: move the DOM node now, reconcile after the server responds.
      if (after) col.insertBefore(node, after);
      else col.append(node);

      if (card.column === columnId && card.position === position) {
        updateCounts();
        return;
      }

      try {
        const updated = await api(`/api/cards/${card.id}/move`, {
          method: "PATCH",
          body: JSON.stringify({ column: columnId, position }),
        });
        Object.assign(card, updated);
        updateCounts();
      } catch (err) {
        console.error(err);
        alert(`Could not move card: ${err.message}`);
        // Roll back to server truth.
        loadBoard().catch(console.error);
      }
    });
  }
}

/* ------------------------------------------------------------------ */
/* Wiring                                                              */
/* ------------------------------------------------------------------ */

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = titleInput.value.trim();
  if (!title) return;

  try {
    const card = await api("/api/cards", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
    const col = boardEl.querySelector('.column[data-column="backlog"]');
    col.append(renderCard(card));
    titleInput.value = "";
    updateCounts();
  } catch (err) {
    console.error(err);
    alert(`Could not create card: ${err.message}`);
  }
});

loadBoard()
  .then(wireColumnDropTargets)
  .catch((err) => {
    console.error(err);
    boardEl.textContent = `Could not load board: ${err.message}`;
  });