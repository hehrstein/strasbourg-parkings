const CARD_TYPE = "strasbourg-parkings-card";

const OCCUPANCY_COLOURS = {
  vert: "#2b9b68",
  green: "#2b9b68",
  orange: "#dc8b22",
  rouge: "#c94a45",
  red: "#c94a45",
};

class StrasbourgParkingsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    const entities = this._entitiesFromConfig(config);
    if (!entities.length) {
      throw new Error("La carte Parkings nécessite une ou plusieurs entités.");
    }

    this._config = {
      max_rows: 6,
      show_capacity: true,
      show_status: true,
      ...config,
      entities,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    const rows = Math.min(this._entitiesFromConfig(this._config).length, this._maxRows());
    return Math.max(3, rows + 2);
  }

  _render() {
    if (!this._config) {
      return;
    }

    const rows = this._rows();
    const missing = this._config.entities.filter((entityId) => !this._hass?.states?.[entityId]);
    const title = this._config.title || "Parkings Strasbourg";
    const updatedAt = this._latestUpdate(rows);

    this.shadowRoot.innerHTML = `
      ${this._styles()}
      <ha-card>
        <header class="card-header">
          <div class="title"><span class="parking-mark" aria-hidden="true">P</span>${this._escape(title)}</div>
          ${updatedAt ? `<div class="updated">Mis à jour à ${this._escape(updatedAt)}</div>` : ""}
        </header>
        ${rows.length ? this._renderRows(rows) : this._renderEmpty(missing)}
        ${missing.length && rows.length ? `<div class="missing">${this._escape(this._missingText(missing))}</div>` : ""}
      </ha-card>
    `;
  }

  _renderRows(rows) {
    return `
      <div class="column-headings" aria-hidden="true"><span>Parking</span><span>Disponibles</span></div>
      <div class="parkings" role="list">${rows.map((row) => this._renderRow(row)).join("")}</div>
      <footer>Données temps réel de l'Eurométropole de Strasbourg</footer>
    `;
  }

  _renderRow(row) {
    const capacity = Number.isFinite(row.capacity) ? row.capacity.toLocaleString("fr-FR") : "—";
    const free = Number.isFinite(row.free) ? row.free.toLocaleString("fr-FR") : "—";
    const occupancy = Number.isFinite(row.occupancy) ? `${Math.round(row.occupancy)} % occupé` : "Occupation non communiquée";
    const status = this._config.show_status && row.status
      ? `<span class="status ${row.isOpen === false ? "closed" : ""}">${this._escape(row.status)}</span>`
      : "";
    const capacityLabel = this._config.show_capacity && capacity !== "—" ? `sur ${capacity}` : "places libres";
    const width = Number.isFinite(row.occupancy) ? Math.max(0, Math.min(100, row.occupancy)) : 0;

    return `
      <article class="parking-row" role="listitem">
        <div class="details">
          <div class="name">${this._escape(row.name)}${status}</div>
          <div class="occupancy"><span class="progress"><span style="width:${width}%;background:${row.colour}"></span></span>${this._escape(occupancy)}</div>
        </div>
        <div class="availability"><strong>${this._escape(free)}</strong><span>${this._escape(capacityLabel)}</span></div>
      </article>
    `;
  }

  _renderEmpty(missing) {
    if (missing.length) {
      return `<div class="empty">${this._escape(this._missingText(missing))}</div>`;
    }
    return '<div class="empty">Aucun parking à afficher.</div>';
  }

  _rows() {
    return this._config.entities
      .map((entityId) => {
        const state = this._hass?.states?.[entityId];
        if (!state) {
          return null;
        }
        const attributes = state.attributes || {};
        const occupancy = Number(attributes.occupancy_percentage);
        const capacity = Number(attributes.total_capacity);
        const free = Number(state.state);
        const status = attributes.status || attributes.display_status || (state.state === "unavailable" ? "Indisponible" : "");
        return {
          name: attributes.parking_name || this._nameFromState(state, "Places disponibles"),
          free: Number.isFinite(free) ? free : null,
          capacity: Number.isFinite(capacity) ? capacity : null,
          occupancy: Number.isFinite(occupancy) ? occupancy : null,
          status,
          isOpen: attributes.status_code === 1 ? true : attributes.status_code === 2 ? false : null,
          colour: OCCUPANCY_COLOURS[String(attributes.occupancy_color || "").toLowerCase()] || "var(--primary-color)",
          updatedAt: attributes.data_updated_at,
        };
      })
      .filter(Boolean)
      .slice(0, this._maxRows());
  }

  _latestUpdate(rows) {
    const dates = rows
      .map((row) => new Date(row.updatedAt))
      .filter((date) => !Number.isNaN(date.getTime()));
    if (!dates.length) {
      return "";
    }
    const latest = new Date(Math.max(...dates.map((date) => date.getTime())));
    return new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit" }).format(latest);
  }

  _entitiesFromConfig(config) {
    const configured = config?.entities || (config?.entity ? [config.entity] : []);
    const values = Array.isArray(configured) ? configured : [configured];
    return values
      .map((item) => typeof item === "string" ? item : item?.entity)
      .filter((item) => typeof item === "string" && item.trim());
  }

  _nameFromState(state, suffix) {
    const name = state.attributes?.friendly_name || state.entity_id;
    return String(name).replace(new RegExp(`\\s*${suffix}$`, "i"), "");
  }

  _missingText(missing) {
    return missing.length === 1
      ? `Entité introuvable : ${missing[0]}`
      : `${missing.length} entités configurées sont introuvables.`;
  }

  _maxRows() {
    const value = Number(this._config?.max_rows);
    return Number.isInteger(value) && value > 0 ? value : 6;
  }

  _escape(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  _styles() {
    return `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; }
        .card-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 18px 14px; border-bottom: 1px solid var(--divider-color); background: color-mix(in srgb, var(--card-background-color) 88%, var(--primary-text-color)); }
        .title { display: flex; align-items: center; gap: 9px; font-size: 15px; font-weight: 700; letter-spacing: .03em; text-transform: uppercase; }
        .parking-mark { display: grid; place-items: center; width: 25px; height: 25px; border-radius: 5px; background: #da6c46; color: #fff; font-size: 18px; font-weight: 800; line-height: 1; }
        .updated { color: var(--secondary-text-color); font-size: 12px; white-space: nowrap; }
        .column-headings { display: flex; justify-content: space-between; padding: 14px 18px 7px; color: var(--secondary-text-color); font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
        .parkings { margin: 0 18px; border-top: 1px solid var(--divider-color); }
        .parking-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 14px; align-items: center; min-height: 72px; border-bottom: 1px solid var(--divider-color); }
        .details { min-width: 0; }
        .name { display: flex; align-items: center; gap: 7px; min-width: 0; overflow: hidden; color: var(--primary-text-color); font-size: 15px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
        .status { flex: 0 0 auto; padding: 2px 6px; border-radius: 10px; color: #1d7d53; background: color-mix(in srgb, #2b9b68 18%, transparent); font-size: 10px; font-weight: 700; }
        .status.closed { color: var(--error-color, #c94a45); background: color-mix(in srgb, #c94a45 17%, transparent); }
        .occupancy { display: flex; align-items: center; gap: 7px; margin-top: 6px; color: var(--secondary-text-color); font-size: 12px; }
        .progress { display: block; width: 58px; height: 5px; overflow: hidden; border-radius: 8px; background: color-mix(in srgb, var(--secondary-text-color) 20%, transparent); }
        .progress span { display: block; height: 100%; border-radius: inherit; }
        .availability { min-width: 78px; text-align: right; font-variant-numeric: tabular-nums; }
        .availability strong { display: block; color: var(--primary-text-color); font-size: 25px; font-weight: 700; letter-spacing: -.04em; line-height: 1; }
        .availability span { display: block; margin-top: 4px; color: var(--secondary-text-color); font-size: 11px; white-space: nowrap; }
        footer { padding: 11px 18px 14px; color: var(--secondary-text-color); font-size: 11px; }
        .empty, .missing { margin: 0 18px 18px; padding: 15px 0; color: var(--secondary-text-color); border-top: 1px solid var(--divider-color); }
        .missing { margin-top: 0; color: var(--warning-color, #bd8500); font-size: 12px; }
        @media (max-width: 480px) {
          .card-header, .column-headings { padding-left: 14px; padding-right: 14px; }
          .parkings, .empty, .missing { margin-left: 14px; margin-right: 14px; }
          footer { padding-left: 14px; padding-right: 14px; }
          .updated { display: none; }
        }
      </style>
    `;
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, StrasbourgParkingsCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === `custom:${CARD_TYPE}`)) {
  window.customCards.push({
    type: `custom:${CARD_TYPE}`,
    name: "Strasbourg Parkings",
    description: "Affiche les places disponibles dans les parkings de Strasbourg.",
  });
}
