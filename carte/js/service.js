// A simulated evening service, to drive the map until the live data exists. Provisional data: the menu, the team
// and the bookings below are placeholders (the fictional restaurant comes later). Deterministic: a seeded random
// generator and fixed 15-second steps, so the same hour always gives the same room.
export const ETATS = {
  libre: { nom: 'Libre', couleur: '#c9c9c7' },
  reservee: { nom: 'Réservée', couleur: '#7c8ce0' },
  installee: { nom: 'Installée, à commander', couleur: '#f0a630' },
  commandee: { nom: 'En attente des plats', couleur: '#3d8bd9' },
  servie: { nom: 'Servie', couleur: '#43a36b' },
  addition: { nom: 'Addition', couleur: '#a672d6' },
  debarrasser: { nom: 'À débarrasser', couleur: '#9b9b98' },
};
export const ALERTE = '#e5484d';
const SEUILS = { installee: 8, commandee: 22 };          // minutes before a table is flagged

const CARTE = {           // provisional menu
  entree: ['Burrata, tomates anciennes', 'Tartare de daurade', 'Velouté de châtaigne', 'Œuf parfait, champignons'],
  plat: ['Risotto aux cèpes', 'Filet de bar, beurre blanc', 'Côte de veau, jus corsé', 'Gnocchis, sauge et parmesan',
    'Pluma ibérique, purée fumée'],
};
const EQUIPE = { tambour: 'Léa', table: 'Hugo', 'table haute': 'Inès', bar: 'Inès' };
const NOMS = ['Martin', 'Bernard', 'Dubois', 'Laurent', 'Moreau', 'Garcia', 'Roux', 'Fournier', 'Lambert', 'Bonnet'];

function graine(a) {       // mulberry32
  return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

export const hhmm = m => `${String(Math.floor(m / 60) % 24).padStart(2, '0')}:${String(Math.floor(m % 60)).padStart(2, '0')}`;

export class Service {
  constructor(tables, { debut = 18 * 60 + 30, heure = 20 * 60 + 10, graine: g = 11 } = {}) {
    this.rnd = graine(g);
    this.t = debut;
    this.tables = tables.filter(t => t.type !== 'bar').map(t => ({ ...t, etat: 'libre', depuis: debut, invites: 0,
      plats: [], commandeA: null, fin: 0, resa: null, alerte: false, serveur: EQUIPE[t.type] }));
    const bar = tables.find(t => t.type === 'bar');
    this.bar = { ...bar, invites: 0, serveur: EQUIPE.bar };
    this.resas = this._reservations();
    this.avancerJusqua(heure);
  }

  _r(a, b) { return a + (b - a) * this.rnd(); }
  _choix(l) { return l[Math.floor(this.rnd() * l.length)]; }

  _reservations() {
    const assises = this.tables;
    const l = [];
    for (let k = 0; k < 7; k++) {
      const t = assises[Math.floor(this.rnd() * assises.length)];
      if (l.some(r => r.table === t.id)) continue;
      l.push({ table: t.id, heure: Math.round(this._r(20 * 60 + 20, 21 * 60 + 40) / 5) * 5, nom: this._choix(NOMS),
        couverts: Math.max(1, Math.min(t.places, Math.round(this._r(2, t.places)))), arrivee: false });
    }
    return l.sort((a, b) => a.heure - b.heure);
  }

  avancerJusqua(m) { while (this.t < m) this.pas(0.25); }

  // dt in simulated minutes
  avancer(dt) {
    this._reste = (this._reste || 0) + dt;
    while (this._reste >= 0.25) { this.pas(0.25); this._reste -= 0.25; }
  }

  _vers(t, etat, duree) { t.etat = etat; t.depuis = this.t; t.fin = this.t + duree; }

  pas(dt) {
    this.t += dt;
    const h = this.t / 60;
    // arrivals: the rush between 19:45 and 21:30
    const affluence = Math.exp(-Math.pow((h - 20.6) / 0.9, 2));
    for (const t of this.tables) {
      const resa = this.resas.find(r => r.table === t.id && !r.arrivee && r.heure - this.t < 30 && r.heure - this.t > -15);
      switch (t.etat) {
        case 'libre':
          if (resa) { this._vers(t, 'reservee', 0); t.resa = resa; break; }
          if (this.rnd() < affluence * dt * 0.035) {
            this._asseoir(t, Math.max(1, Math.min(t.places, Math.round(this._r(1.6, t.places + 0.4)))));
          }
          break;
        case 'reservee':
          if (this.t >= t.resa.heure - 3 && this.rnd() < dt * 0.25) {
            t.resa.arrivee = true; this._asseoir(t, t.resa.couverts);
          } else if (this.t > t.resa.heure + 15) { t.resa.arrivee = true; t.resa = null; this._vers(t, 'libre', 0); }
          break;
        case 'installee':
          if (this.t >= t.fin) this._commander(t);
          break;
        case 'commandee': {
          for (const p of t.plats) if (!p.servi && this.t >= p.pret + 1.5) p.servi = true;
          if (t.plats.every(p => p.servi)) this._vers(t, 'servie', this._r(26, 44));
          break;
        }
        case 'servie':
          if (this.t >= t.fin) this._vers(t, 'addition', this._r(5, 12));
          break;
        case 'addition':
          if (this.t >= t.fin) { t.invites = 0; t.plats = []; t.commandeA = null; t.resa = null;
            this._vers(t, 'debarrasser', this._r(3, 7)); }
          break;
        case 'debarrasser':
          if (this.t >= t.fin) this._vers(t, 'libre', 0);
          break;
      }
      const attente = this.t - t.depuis;
      t.alerte = (t.etat === 'installee' && attente > SEUILS.installee) || (t.etat === 'commandee' && attente > SEUILS.commandee);
    }
    // the bar: people come and go one by one
    const cible = Math.round(7 * Math.min(1, 0.25 + affluence * 0.75));
    if (this.rnd() < dt * 0.3) this.bar.invites = Math.max(0, Math.min(7, this.bar.invites + (this.bar.invites < cible ? 1 : -1)));
  }

  _asseoir(t, n) {
    t.invites = n; t.plats = []; t.commandeA = null;
    this._vers(t, 'installee', this._r(3, 10));
  }

  _commander(t) {
    t.commandeA = this.t;
    for (let k = 0; k < t.invites; k++) {
      if (this.rnd() < 0.45) t.plats.push({ nom: this._choix(CARTE.entree), pret: this.t + this._r(9, 15), servi: false });
      t.plats.push({ nom: this._choix(CARTE.plat), pret: this.t + this._r(15, 27), servi: false });
    }
    this._vers(t, 'commandee', 0);
  }

  // ---- what the panels show
  statutPlat(p) { return p.servi ? 'servi' : this.t >= p.pret ? 'pret' : 'cuisine'; }
  attente(t) { return this.t - t.depuis; }

  chiffres() {
    const T = this.tables, places = T.reduce((s, t) => s + t.places, 0) + this.bar.places;
    const couverts = T.reduce((s, t) => s + t.invites, 0) + this.bar.invites;
    const cmd = T.filter(t => t.etat === 'commandee');
    const parEtat = Object.fromEntries(Object.keys(ETATS).map(e => [e, T.filter(t => t.etat === e).length]));
    const prochaine = this.resas.find(r => !r.arrivee && r.heure >= this.t - 15);
    return { couverts, places, parEtat, libres: parEtat.libre, total: T.length,
      attente: cmd.length ? cmd.reduce((s, t) => s + (this.t - t.depuis), 0) / cmd.length : 0, enAttente: cmd.length,
      alertes: T.filter(t => t.alerte).length, bar: this.bar.invites, prochaine };
  }
}
